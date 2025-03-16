from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from typing import Dict, List, Optional, Set
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
from bs4 import BeautifulSoup
import os

# Setup Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# Add these new options to suppress warnings
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")  # Only show fatal errors
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

# Initialize the driver (make sure you have chromedriver installed)
driver = webdriver.Chrome(options=chrome_options)

def scrape_significant_strikes_per_round(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    # Step A: Find <th> elements that say "Round 1," "Round 2," etc.
    round_ths = soup.find_all("th", string=re.compile(r"Round\s+\d+"))
    if not round_ths:
        print("No <th> elements found matching 'Round X'. Check your HTML or selectors.")
        return []

    all_round_data = []
    for th in round_ths:
        # Extract round # (e.g. "Round 2" -> 2)
        round_text = th.get_text(strip=True)
        match = re.search(r"Round\s+(\d+)", round_text)
        if not match:
            continue
        round_number = int(match.group(1))

        # The <th> is inside a <thead>; typically, the next <tbody> holds the data row
        round_thead = th.find_parent("thead")
        if not round_thead:
            continue

        data_tbody = round_thead.find_next_sibling("tbody")
        if not data_tbody:
            print(f"No <tbody> found after thead for round {round_number}")
            continue

        # Usually just one .b-fight-details__table-row in that <tbody>
        data_row = data_tbody.find("tr", class_="b-fight-details__table-row")
        if not data_row:
            print(f"No data row found under round {round_number}")
            continue

        # Now we expect 9 <td> columns for the standard "Significant Strikes" layout
        tds = data_row.find_all("td", class_="b-fight-details__table-col")
        if len(tds) != 9:
            #print(f"Round {round_number}: expected 9 columns, got {len(tds)}. Skipping.")
            continue

        # Columns:
        # 0: Fighter
        # 1: Sig. Str
        # 2: Sig. Str. %
        # 3: Head
        # 4: Body
        # 5: Leg
        # 6: Distance
        # 7: Clinch
        # 8: Ground

        fighter_names     = [p.get_text(strip=True) for p in tds[0].find_all("p")]
        sig_str_list      = [p.get_text(strip=True) for p in tds[1].find_all("p")]
        sig_str_pct_list  = [p.get_text(strip=True) for p in tds[2].find_all("p")]
        head_list         = [p.get_text(strip=True) for p in tds[3].find_all("p")]
        body_list         = [p.get_text(strip=True) for p in tds[4].find_all("p")]
        leg_list          = [p.get_text(strip=True) for p in tds[5].find_all("p")]
        distance_list     = [p.get_text(strip=True) for p in tds[6].find_all("p")]
        clinch_list       = [p.get_text(strip=True) for p in tds[7].find_all("p")]
        ground_list       = [p.get_text(strip=True) for p in tds[8].find_all("p")]

        # Build two entries (one per fighter)
        for i in range(2):
            single_fighter = {
                "round": round_number,
                "fighter": fighter_names[i]      if i<len(fighter_names)     else "",
                "sig_str": sig_str_list[i]       if i<len(sig_str_list)      else "",
                "sig_str_pct": sig_str_pct_list[i] if i<len(sig_str_pct_list)  else "",
                "head": head_list[i]            if i<len(head_list)         else "",
                "body": body_list[i]            if i<len(body_list)         else "",
                "leg": leg_list[i]              if i<len(leg_list)          else "",
                "distance": distance_list[i]     if i<len(distance_list)     else "",
                "clinch": clinch_list[i]        if i<len(clinch_list)       else "",
                "ground": ground_list[i]        if i<len(ground_list)       else "",
            }
            all_round_data.append(single_fighter)

    return all_round_data

def extract_fight_details(soup: BeautifulSoup) -> Dict:
    """Extract basic fight information"""
    fight_details = {}
    
    # Get event name and date
    event_link = soup.select_one('h2.b-content__title a')
    if event_link:
        fight_details['event_name'] = event_link.text.strip()
    
    # Get fight title/type (e.g., "UFC Lightweight Title Bout")
    fight_type = soup.select_one('div.b-fight-details__fight-head i.b-fight-details__fight-title')
    if fight_type:
        fight_details['fight_type'] = fight_type.text.strip()
    
    # Get fight details from the content div
    details_box = soup.select_one('div.b-fight-details__content')
    if details_box:
        # Method
        method_item = details_box.select_one('i.b-fight-details__text-item_first i[style="font-style: normal"]')
        if method_item:
            fight_details['method'] = method_item.text.strip()
        
        # Round
        round_label = details_box.find('i', class_='b-fight-details__label', string=lambda x: 'Round:' in str(x))
        if round_label:
            round_text = round_label.next_sibling
            if round_text:
                fight_details['final_round'] = round_text.strip()
        
        # Time
        time_label = details_box.find('i', class_='b-fight-details__label', string=lambda x: 'Time:' in str(x))
        if time_label:
            time_text = time_label.next_sibling
            if time_text:
                fight_details['final_time'] = time_text.strip()
        
        # Time format
        format_label = details_box.find('i', class_='b-fight-details__label', string=lambda x: 'Time format:' in str(x))
        if format_label:
            format_text = format_label.next_sibling
            if format_text:
                fight_details['time_format'] = format_text.strip()
        
        # Referee
        referee_label = details_box.find('i', class_='b-fight-details__label', string=lambda x: 'Referee:' in str(x))
        if referee_label:
            referee_span = referee_label.find_next('span')
            if referee_span:
                fight_details['referee'] = referee_span.text.strip()
        
        # Details (finish details)
        details_label = details_box.find('i', class_='b-fight-details__label', string=lambda x: 'Details:' in str(x))
        if details_label:
            details_text = details_label.parent.next_sibling
            if details_text:
                fight_details['finish_details'] = details_text.strip()
    
    # Get fighter names and status (winner/loser)
    fighters = soup.select('div.b-fight-details__person')
    for i, fighter in enumerate(fighters):
        prefix = 'red' if i == 0 else 'blue'
        
        # Get status (W/L)
        status = fighter.select_one('i.b-fight-details__person-status')
        if status:
            fight_details[f'{prefix}_fighter_status'] = status.text.strip()
        
        # Get name
        name = fighter.select_one('h3.b-fight-details__person-name a')
        if name:
            fight_details[f'{prefix}_fighter_name'] = name.text.strip()
            fight_details[f'{prefix}_fighter_link'] = name['href']
    
    return fight_details

def extract_round_stats(soup: BeautifulSoup, round_num: int) -> Dict:
    """
    Extract statistics for a specific round. This scrapes:
    - Knockdowns (KD)
    - Significant Strikes (landed/attempted + percentage)
    - Total Strikes
    - Takedowns (landed/attempted + percentage)
    - Submission Attempts
    - Reversals
    - Control Time
    - And then, in a second pass, location-based significant strikes:
      (Head, Body, Leg, Distance, Clinch, Ground)
    """

    round_stats = {}

    # ---------------------------------------
    # 1) BASIC STATS TABLE (KD, SIG STR, ETC.)
    # ---------------------------------------
    # There is usually a <thead class="b-fight-details__table-row b-fight-details__table-row_type_head">
    # with "Round N" text. Immediately after comes a <tr> with the stats.
    round_headers = soup.find_all('thead', class_='b-fight-details__table-row b-fight-details__table-row_type_head')
    round_header = None
    for header in round_headers:
        if header.text.strip() == f'Round {round_num}':
            round_header = header
            break

    if round_header:
        # Get the next table row, which should contain the stats for that round
        stats_row = round_header.find_next('tr', class_='b-fight-details__table-row')
        if stats_row:
            cells = stats_row.find_all('td', class_='b-fight-details__table-col')
            # Ensure we have at least 10 cells in that row (KD, SIG STR, SIG %, Total Str, TD, TD %, Sub, Rev, Ctrl, etc.)
            if len(cells) >= 10:
                try:
                    # KD
                    kd_values = cells[1].find_all('p', class_='b-fight-details__table-text')
                    if len(kd_values) >= 2:
                        round_stats[f'red_r{round_num}_kd'] = kd_values[0].text.strip()
                        round_stats[f'blue_r{round_num}_kd'] = kd_values[1].text.strip()

                    # Significant Strikes
                    sig_str_values = cells[2].find_all('p', class_='b-fight-details__table-text')
                    if len(sig_str_values) >= 2:
                        red_sig = sig_str_values[0].text.strip().split('of')
                        blue_sig = sig_str_values[1].text.strip().split('of')
                        if len(red_sig) == 2:
                            round_stats[f'red_r{round_num}_sig_str_landed'] = red_sig[0].strip()
                            round_stats[f'red_r{round_num}_sig_str_attempted'] = red_sig[1].strip()
                        if len(blue_sig) == 2:
                            round_stats[f'blue_r{round_num}_sig_str_landed'] = blue_sig[0].strip()
                            round_stats[f'blue_r{round_num}_sig_str_attempted'] = blue_sig[1].strip()

                    # Sig Strike Percentage
                    sig_pct_values = cells[3].find_all('p', class_='b-fight-details__table-text')
                    if len(sig_pct_values) >= 2:
                        round_stats[f'red_r{round_num}_sig_str_pct'] = sig_pct_values[0].text.strip().replace('%', '')
                        round_stats[f'blue_r{round_num}_sig_str_pct'] = sig_pct_values[1].text.strip().replace('%', '')

                    # Total Strikes
                    total_str_values = cells[4].find_all('p', class_='b-fight-details__table-text')
                    if len(total_str_values) >= 2:
                        red_total = total_str_values[0].text.strip().split('of')
                        blue_total = total_str_values[1].text.strip().split('of')
                        if len(red_total) == 2:
                            round_stats[f'red_r{round_num}_total_str_landed'] = red_total[0].strip()
                            round_stats[f'red_r{round_num}_total_str_attempted'] = red_total[1].strip()
                        if len(blue_total) == 2:
                            round_stats[f'blue_r{round_num}_total_str_landed'] = blue_total[0].strip()
                            round_stats[f'blue_r{round_num}_total_str_attempted'] = blue_total[1].strip()

                    # Takedowns
                    td_values = cells[5].find_all('p', class_='b-fight-details__table-text')
                    if len(td_values) >= 2:
                        red_td = td_values[0].text.strip().split('of')
                        blue_td = td_values[1].text.strip().split('of')
                        if len(red_td) == 2:
                            round_stats[f'red_r{round_num}_td_landed'] = red_td[0].strip()
                            round_stats[f'red_r{round_num}_td_attempted'] = red_td[1].strip()
                        if len(blue_td) == 2:
                            round_stats[f'blue_r{round_num}_td_landed'] = blue_td[0].strip()
                            round_stats[f'blue_r{round_num}_td_attempted'] = blue_td[1].strip()

                    # TD Percentage
                    td_pct_values = cells[6].find_all('p', class_='b-fight-details__table-text')
                    if len(td_pct_values) >= 2:
                        round_stats[f'red_r{round_num}_td_pct'] = td_pct_values[0].text.strip().replace('%', '')
                        round_stats[f'blue_r{round_num}_td_pct'] = td_pct_values[1].text.strip().replace('%', '')

                    # Submission Attempts
                    sub_values = cells[7].find_all('p', class_='b-fight-details__table-text')
                    if len(sub_values) >= 2:
                        round_stats[f'red_r{round_num}_sub_att'] = sub_values[0].text.strip()
                        round_stats[f'blue_r{round_num}_sub_att'] = sub_values[1].text.strip()

                    # Reversals
                    rev_values = cells[8].find_all('p', class_='b-fight-details__table-text')
                    if len(rev_values) >= 2:
                        round_stats[f'red_r{round_num}_rev'] = rev_values[0].text.strip()
                        round_stats[f'blue_r{round_num}_rev'] = rev_values[1].text.strip()

                    # Control Time
                    ctrl_values = cells[9].find_all('p', class_='b-fight-details__table-text')
                    if len(ctrl_values) >= 2:
                        round_stats[f'red_r{round_num}_ctrl'] = ctrl_values[0].text.strip()
                        round_stats[f'blue_r{round_num}_ctrl'] = ctrl_values[1].text.strip()

                except Exception as e:
                    print(f"Error processing basic stats for round {round_num}: {e}")

    # print(round_stats)

    return round_stats

def extract_fighter_details(fighter_url: str) -> Dict:
    """Extract fighter physical details and stats from their profile page"""
    try:
        response = requests.get(fighter_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        fighter_details = {}
        
        # Find the info box containing physical details
        info_box = soup.select_one('div.b-list__info-box_style_small-width')
        if info_box:
            # Extract each detail using the title as the key
            for item in info_box.select('li.b-list__box-list-item'):
                title = item.select_one('i.b-list__box-item-title')
                if title:
                    key = title.text.strip().lower().replace(':', '')
                    value = item.get_text(strip=True).replace(title.text, '').strip()
                    
                    # Convert keys to match expected format
                    if key == 'height':
                        fighter_details['height'] = value.replace('Height:', '').strip()
                    elif key == 'weight':
                        fighter_details['weight'] = value.replace('Weight:', '').replace('lbs.', '').strip()
                    elif key == 'reach':
                        fighter_details['reach'] = value.replace('Reach:', '').replace('"', '').strip()
                    elif key == 'stance':
                        fighter_details['stance'] = value.replace('STANCE:', '').strip()
                    elif key == 'dob':
                        fighter_details['dob'] = value.replace('DOB:', '').strip()
        
        return fighter_details
    
    except Exception as e:
        print(f"Error fetching fighter details from {fighter_url}: {e}")
        return {}

def scrape_fight_data(fight_url: str) -> Optional[Dict]:
    """Scrape all data for a single fight"""
    try:
        response = requests.get(fight_url)
        response.raise_for_status()
        
        # Get the HTML content and create soup object
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get basic fight details first
        fight_data = extract_fight_details(soup)
        
        # Add fight URL
        fight_data['fight_url'] = fight_url
        
        # Store fighter details separately to prevent overwriting
        fighter_details = {}
        
        # Get fighter details for both fighters
        if 'red_fighter_link' in fight_data:
            red_details = extract_fighter_details(fight_data['red_fighter_link'])
            fighter_details['red_fighter_reach'] = red_details.get('reach')
            fighter_details['red_fighter_height'] = red_details.get('height')
            fighter_details['red_fighter_weight'] = red_details.get('weight')
            fighter_details['red_fighter_stance'] = red_details.get('stance')
            fighter_details['red_fighter_dob'] = red_details.get('dob')
            
        if 'blue_fighter_link' in fight_data:
            blue_details = extract_fighter_details(fight_data['blue_fighter_link'])
            fighter_details['blue_fighter_reach'] = blue_details.get('reach')
            fighter_details['blue_fighter_height'] = blue_details.get('height')
            fighter_details['blue_fighter_weight'] = blue_details.get('weight')
            fighter_details['blue_fighter_stance'] = blue_details.get('stance')
            fighter_details['blue_fighter_dob'] = blue_details.get('dob')
        
        # Get round-by-round stats
        for round_num in range(1, 6):
            round_stats = extract_round_stats(soup, round_num)
            if round_stats:
                fight_data.update(round_stats)
        
        # Add fighter details after round stats to ensure they're not overwritten
        fight_data.update(fighter_details)
    
        response = requests.get(fight_url)
        response.raise_for_status()
        
        # Get the HTML content and create soup object
        html_content = response.content.decode('utf-8')
    

        driver.get(fight_url)
        time.sleep(0.5)
        html_content = driver.page_source

        sig_strikes_data = scrape_significant_strikes_per_round(html_content)
        
        # Convert the sig strikes data into the format matching our DataFrame
        for round_data in sig_strikes_data:
            round_num = round_data['round']
            fighter_name = round_data['fighter'].strip()
            red_fighter_name = fight_data.get('red_fighter_name', '').strip()
            
            # Determine prefix based on exact fighter name match
            prefix = 'red' if fighter_name == red_fighter_name else 'blue'
            
            # Helper function to safely split "X of Y" values
            def split_strike_value(value):
                try:
                    return value.split(' of ')
                except:
                    return ['0', '0']
            
            # Add the significant strikes data with proper column names
            fight_data.update({
                f'{prefix}_r{round_num}_sig_str_landed': split_strike_value(round_data['sig_str'])[0],
                f'{prefix}_r{round_num}_sig_str_attempted': split_strike_value(round_data['sig_str'])[1],
                f'{prefix}_r{round_num}_sig_str_pct': round_data['sig_str_pct'].replace('%', ''),
                f'{prefix}_r{round_num}_head_landed': split_strike_value(round_data['head'])[0],
                f'{prefix}_r{round_num}_head_attempted': split_strike_value(round_data['head'])[1],
                f'{prefix}_r{round_num}_body_landed': split_strike_value(round_data['body'])[0],
                f'{prefix}_r{round_num}_body_attempted': split_strike_value(round_data['body'])[1],
                f'{prefix}_r{round_num}_leg_landed': split_strike_value(round_data['leg'])[0],
                f'{prefix}_r{round_num}_leg_attempted': split_strike_value(round_data['leg'])[1],
                f'{prefix}_r{round_num}_distance_landed': split_strike_value(round_data['distance'])[0],
                f'{prefix}_r{round_num}_distance_attempted': split_strike_value(round_data['distance'])[1],
                f'{prefix}_r{round_num}_clinch_landed': split_strike_value(round_data['clinch'])[0],
                f'{prefix}_r{round_num}_clinch_attempted': split_strike_value(round_data['clinch'])[1],
                f'{prefix}_r{round_num}_ground_landed': split_strike_value(round_data['ground'])[0],
                f'{prefix}_r{round_num}_ground_attempted': split_strike_value(round_data['ground'])[1],
            })

        
        return fight_data
    
    except Exception as e:
        print(f"Error fetching fight data from {fight_url}: {e}")
        return None

def get_already_processed_fights(output_file: str) -> Set[str]:
    """
    Check if the output file exists and extract the fight URLs that have already been processed.
    Returns a set of fight URLs that should be skipped.
    """
    processed_fights = set()
    
    if os.path.exists(output_file):
        try:
            print(f"Found existing data file: {output_file}")
            # Read the file efficiently - only load the fight_url column
            existing_data = pd.read_excel(output_file, usecols=['fight_url'])
            
            # Extract unique fight URLs
            processed_fights = set(existing_data['fight_url'].unique())
            print(f"Found {len(processed_fights)} already processed fights")
        except Exception as e:
            print(f"Error reading existing data file: {e}")
    else:
        print(f"No existing data file found at {output_file}")
    
    return processed_fights

def process_fights(fight_urls: List[str], processed_fights: Set[str] = None, max_fights: Optional[int] = None) -> pd.DataFrame:
    """Process multiple fights and return as DataFrame with rounds as separate rows"""
    all_fights_data = []
    
    # Initialize processed_fights if not provided
    if processed_fights is None:
        processed_fights = set()
    
    # Filter out already processed fights
    new_fight_urls = [url for url in fight_urls if url not in processed_fights]
    
    # Limit number of fights if specified
    if max_fights:
        new_fight_urls = new_fight_urls[:max_fights]
    
    total_fights = len(new_fight_urls)
    print(f"Found {total_fights} new fights to process out of {len(fight_urls)} total fights")
    
    for i, url in enumerate(new_fight_urls, 1):
        print(f"\rProcessing fight {i}/{total_fights} ({url})... ")
        fight_data = scrape_fight_data(url)
        
        if fight_data:
            # Get the maximum round number from the data
            round_numbers = []
            for key in fight_data.keys():
                match = re.search(r'_r(\d+)_', key)
                if match:
                    round_numbers.append(int(match.group(1)))
            
            max_round = max(round_numbers) if round_numbers else 0
            
            # Base fight details (non-round specific data)
            base_fight_data = {k: v for k, v in fight_data.items() if '_r' not in k}
            
            # Ensure fighter details are included in base data
            fighter_cols = ['red_fighter_reach', 'red_fighter_height', 'red_fighter_weight', 
                          'red_fighter_stance', 'red_fighter_dob', 'blue_fighter_reach', 
                          'blue_fighter_height', 'blue_fighter_weight', 'blue_fighter_stance', 
                          'blue_fighter_dob']
            for col in fighter_cols:
                if col in fight_data:
                    base_fight_data[col] = fight_data[col]
            
            # Create a row for each round
            for round_num in range(1, max_round + 1):
                round_data = base_fight_data.copy()
                round_data['round'] = round_num
                
                # Extract all stats for this specific round
                for key, value in fight_data.items():
                    if f'_r{round_num}_' in key:
                        new_key = key.replace(f'_r{round_num}_', '_')
                        round_data[new_key] = value
                
                all_fights_data.append(round_data)
        
        time.sleep(0.5)  # Be nice to the server
    
    if not all_fights_data:
        print("No new fights to process.")
        return pd.DataFrame()
    
    print("Creating DataFrame...")
    df = pd.DataFrame(all_fights_data)
    
    # Get actual columns from the DataFrame
    match_cols = [col for col in ['event_name', 'fight_type', 'method', 'time_format', 
                                 'referee', 'finish_details'] if col in df.columns]
    fighter_cols = [col for col in fighter_cols if col in df.columns]
    round_col = ['round']
    stat_cols = [col for col in df.columns if col not in match_cols + fighter_cols + round_col]
    
    # Reorder columns only if they exist
    df = df[match_cols + fighter_cols + round_col + sorted(stat_cols)]
    
    return df

def main():
    # from UFC_events import main as events_main
    # events = events_main()
    # fight_urls = events['fight_link'].tolist()

    # Define output file path
    output_file = 'data/ufc_fight_details.xlsx'
    
    # Get already processed fights
    processed_fights = get_already_processed_fights(output_file)
    
    # Get all fight URLs from events file
    events = pd.read_excel('data/ufc_events.xlsx')
    fight_urls = events['fight_link'].tolist()
    
    # Process only new fights
    new_data = process_fights(
        fight_urls,
        processed_fights=processed_fights,
        #max_fights=2
    )
    
    # If we have new data, merge with existing data and save
    if not new_data.empty:
        if os.path.exists(output_file):
            # Load existing data
            existing_data = pd.read_excel(output_file)
            
            # Concatenate with new data
            combined_data = pd.concat([existing_data, new_data], ignore_index=True)
            print(f"Combined {len(existing_data)} existing rows with {len(new_data)} new rows")
            
            # Save the combined data
            combined_data.to_excel(output_file, index=False)
            print(f"\nData saved to {output_file}")
            
            # Display summary
            print(f"\nTotal: {len(combined_data)} rounds from {len(combined_data['fight_url'].unique())} fights")
        else:
            # Just save the new data if no existing file
            new_data.to_excel(output_file, index=False)
            print(f"\nData saved to {output_file}")
            
            # Display summary
            print(f"\nProcessed {len(new_data)} rounds from {len(new_data['fight_url'].unique())} fights")
    else:
        print("\nNo new data to save.")
    
    print("\nColumns in dataset:")
    if not new_data.empty:
        print(new_data.columns.tolist())
    elif os.path.exists(output_file):
        existing_data = pd.read_excel(output_file)
        print(existing_data.columns.tolist())

if __name__ == "__main__":
    main()