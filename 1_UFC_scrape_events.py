from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
import argparse
import os
from typing import Set, List, Dict, Optional

def scrape_fight_links_from_event(event_url):
    """Scrape all fight links from a specific event page"""
    try:
        response = requests.get(event_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all fight rows
        fight_rows = soup.select('tr.b-fight-details__table-row[data-link]')
        
        fights = []
        for row in fight_rows:
            # Get fight link
            fight_link = row.get('data-link')
            
            # Get fighter names
            fighter_links = row.select('td a.b-link.b-link_style_black')
            fighter_names = [link.text.strip() for link in fighter_links]
            
            # Get weight class
            weight_class = row.select_one('td.b-fight-details__table-col p.b-fight-details__table-text')
            weight_class = weight_class.text.strip() if weight_class else None
            
            # Get method of victory
            method = row.select('td.b-fight-details__table-col')[7].text.strip()
            
            fights.append({
                'fighter1': fighter_names[0] if len(fighter_names) > 0 else None,
                'fighter2': fighter_names[1] if len(fighter_names) > 1 else None,
                'weight_class': weight_class,
                'method': method,
                'fight_link': fight_link
            })
            
        return fights
    
    except requests.RequestException as e:
        print(f"Error fetching event {event_url}: {e}")
        return []

def get_already_processed_events(output_file: str) -> Set[str]:
    """
    Check if the output file exists and extract the event links that have already been processed.
    Returns a set of event links that should be skipped.
    """
    processed_events = set()
    
    if os.path.exists(output_file):
        try:
            print(f"Found existing data file: {output_file}")
            # Read the file efficiently - only load the event_link column
            existing_data = pd.read_excel(output_file)
            
            # Check if event_link column exists
            if 'event_link' in existing_data.columns:
                # Extract unique event links
                processed_events = set(existing_data['event_link'].unique())
                print(f"Found {len(processed_events)} already processed events")
                
                # Debug: Print first few event links to verify
                if processed_events:
                    print("Sample of processed event links:")
                    for link in list(processed_events)[:3]:
                        print(f"  - {link}")
            else:
                print(f"Warning: 'event_link' column not found in {output_file}")
                print(f"Available columns: {existing_data.columns.tolist()}")
        except Exception as e:
            print(f"Error reading existing data file: {e}")
    else:
        print(f"No existing data file found at {output_file}")
    
    return processed_events

def get_already_processed_fights(output_file: str) -> Set[str]:
    """
    Check if the output file exists and extract the fight links that have already been processed.
    Returns a set of fight links that should be skipped.
    """
    processed_fights = set()
    
    if os.path.exists(output_file):
        try:
            print(f"Found existing data file: {output_file}")
            # Read the file efficiently
            existing_data = pd.read_excel(output_file)
            
            # Check if fight_link column exists
            if 'fight_link' in existing_data.columns:
                # Extract unique fight links
                processed_fights = set(existing_data['fight_link'].unique())
                print(f"Found {len(processed_fights)} already processed fights")
                
                # Debug: Print first few fight links to verify
                if processed_fights:
                    print("Sample of processed fight links:")
                    for link in list(processed_fights)[:3]:
                        print(f"  - {link}")
            else:
                print(f"Warning: 'fight_link' column not found in {output_file}")
                print(f"Available columns: {existing_data.columns.tolist()}")
        except Exception as e:
            print(f"Error reading existing data file: {e}")
    else:
        print(f"No existing data file found at {output_file}")
    
    return processed_fights

def get_already_processed_upcoming_events(output_file: str) -> Set[str]:
    """
    Check if the output file exists and extract the event names that have already been processed.
    Returns a set of event names that should be skipped.
    """
    processed_events = set()
    
    if os.path.exists(output_file):
        try:
            print(f"Found existing data file: {output_file}")
            # Read the file efficiently - only load the event_name column
            existing_data = pd.read_excel(output_file, usecols=['event_name'])
            
            # Extract unique event names
            processed_events = set(existing_data['event_name'].unique())
            print(f"Found {len(processed_events)} already processed upcoming events")
        except Exception as e:
            print(f"Error reading existing data file: {e}")
    else:
        print(f"No existing data file found at {output_file}")
    
    return processed_events

def scrape_ufc_fights(num_events=None, processed_events=None, processed_fights=None):
    """
    Scrape UFC fights from events
    
    Parameters:
    num_events (int, optional): Number of events to scrape. If None, scrapes all events.
    processed_events (Set[str], optional): Set of event links that have already been processed.
    processed_fights (Set[str], optional): Set of fight links that have already been processed.
    """
    # Initialize sets if not provided
    if processed_events is None:
        processed_events = set()
    if processed_fights is None:
        processed_fights = set()
    
    print(f"Starting scrape_ufc_fights with {len(processed_events)} processed events and {len(processed_fights)} processed fights")
    
    # First get all events
    events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    
    try:
        response = requests.get(events_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all event links
        event_rows = soup.select('tr.b-statistics__table-row')
        
        # Remove the first row (upcoming event)
        event_rows = event_rows[1:]
        
        # Limit number of events if specified
        if num_events:
            event_rows = event_rows[:num_events]
            print(f"Scraping the first {num_events} events...")
        else:
            print("Scraping all events...")
            
        all_fights = []
        total_events = len(event_rows)
        new_events_count = 0
        skipped_events_count = 0
        
        print(f"Found {total_events} total events to process")
        
        for idx, row in enumerate(event_rows, 1):
            event_link = row.select_one('td a.b-link')
            if event_link:
                event_url = event_link['href']
                event_name = event_link.text.strip()
                event_date = row.select_one('span.b-statistics__date')
                event_date = event_date.text.strip() if event_date else None
                
                # Skip if event has already been processed
                if event_url in processed_events:
                    print(f"Skipping already processed event: {event_name} ({idx}/{total_events})")
                    skipped_events_count += 1
                    continue
                
                new_events_count += 1
                print(f"Scraping fights from: {event_name} ({idx}/{total_events})")
                
                # Get all fights from this event
                fights = scrape_fight_links_from_event(event_url)
                print(f"  Found {len(fights)} fights in this event")
                
                # Filter out already processed fights
                new_fights = []
                skipped_fights = 0
                for fight in fights:
                    if fight['fight_link'] not in processed_fights:
                        fight['event_name'] = event_name
                        fight['event_date'] = event_date
                        fight['event_link'] = event_url
                        new_fights.append(fight)
                    else:
                        skipped_fights += 1
                        print(f"  Skipping already processed fight: {fight['fighter1']} vs {fight['fighter2']}")
                
                all_fights.extend(new_fights)
                print(f"  Added {len(new_fights)} new fights from this event (skipped {skipped_fights})")
                
                # Add delay to avoid overwhelming the server
                time.sleep(0.1)
        
        print(f"Processed {new_events_count} new events out of {total_events} total events (skipped {skipped_events_count})")
        print(f"Found {len(all_fights)} new fights")
        
        # Create DataFrame
        df = pd.DataFrame(all_fights) if all_fights else pd.DataFrame()
        
        # Debug the resulting DataFrame
        debug_dataframe(df, "Scraped UFC fights")
        
        return df
        
    except requests.RequestException as e:
        print(f"Error fetching events: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def scrape_upcoming(processed_event_names=None):
    """
    Scrape upcoming UFC events and their fights
    
    Parameters:
    processed_event_names (Set[str], optional): Set of event names that have already been processed.
    """
    if processed_event_names is None:
        processed_event_names = set()
    
    print(f"Starting scrape_upcoming with {len(processed_event_names)} processed event names")
        
    events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    
    try:
        response = requests.get(events_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first row (upcoming event)
        event_row = soup.select_one('tr.b-statistics__table-row_type_first')
        if not event_row:
            print("No upcoming events found")
            return pd.DataFrame()
            
        # Extract event details
        event_link = event_row.select_one('a.b-link')
        if not event_link:
            print("No event link found in the upcoming event row")
            return pd.DataFrame()
            
        event_url = event_link['href']
        event_name = event_link.text.strip()
        
        print(f"Found upcoming event: {event_name} at URL: {event_url}")
        
        # Skip if event has already been processed
        if event_name in processed_event_names:
            print(f"Skipping already processed upcoming event: {event_name}")
            return pd.DataFrame()
            
        event_date = event_row.select_one('span.b-statistics__date')
        event_date = event_date.text.strip() if event_date else None
        event_location = event_row.select_one('td.b-statistics__table-col_style_big-top-padding')
        event_location = event_location.text.strip() if event_location else None
        
        print(f"Scraping upcoming event: {event_name} on {event_date} at {event_location}")
        
        # Get the event page to scrape individual fights
        event_response = requests.get(event_url)
        event_response.raise_for_status()
        event_soup = BeautifulSoup(event_response.text, 'html.parser')
        
        # Find all fight rows
        fight_rows = event_soup.select('tr.b-fight-details__table-row[data-link]')
        
        print(f"Found {len(fight_rows)} fights in the upcoming event")
        
        fights = []
        for row in fight_rows:
            # Get fighter names
            fighter_links = row.select('td a.b-link.b-link_style_black')
            fighter_names = [link.text.strip() for link in fighter_links]
            
            # Get weight class
            weight_class = row.select_one('td.b-fight-details__table-col p.b-fight-details__table-text')
            weight_class = weight_class.text.strip() if weight_class else None
            
            # Get fight link
            fight_link = row.get('data-link')
            
            fight_data = {
                'event_name': event_name,
                'event_date': event_date,
                'event_location': event_location,
                'event_link': event_url,
                'fight_link': fight_link,
                'fighter1': fighter_names[0] if len(fighter_names) > 0 else None,
                'fighter2': fighter_names[1] if len(fighter_names) > 1 else None,
                'weight_class': weight_class
            }
            
            fights.append(fight_data)
            print(f"  Added fight: {fight_data['fighter1']} vs {fight_data['fighter2']}")
        
        # Create DataFrame
        df = pd.DataFrame(fights)
        
        if df.empty:
            print("No fights found for the upcoming event")
            return pd.DataFrame()
            
        # Reorder columns
        cols = ['event_name', 'event_date', 'event_location', 'event_link', 
                'fighter1', 'fighter2', 'weight_class', 'fight_link']
        df = df[cols]
        
        print(f"Found {len(df)} fights for {event_name}")
        
        # Debug the resulting DataFrame
        debug_dataframe(df, "Upcoming UFC fights")
        
        return df
        
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def scrape_fight_details(fight_df: pd.DataFrame, processed_fights=None) -> pd.DataFrame:
    """
    Scrape detailed fight information for each fight in the DataFrame
    
    Parameters:
    fight_df (pd.DataFrame): DataFrame containing fight_link column
    processed_fights (Set[str], optional): Set of fight links that have already been processed.
    
    Returns:
    pd.DataFrame: Original DataFrame with additional fight detail columns
    """
    if processed_fights is None:
        processed_fights = set()
        
    detailed_fights = []
    
    for _, row in fight_df.iterrows():
        try:
            fight_link = row['fight_link']
            
            # Skip if fight has already been processed
            if fight_link in processed_fights:
                print(f"Skipping already processed fight details: {row['fighter1']} vs {row['fighter2']}")
                continue
                
            print(f"Scraping fight details: {row['fighter1']} vs {row['fighter2']}")
            
            response = requests.get(fight_link)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Initialize fight data with existing row data
            fight_data = row.to_dict()
            
            # Get weight class from the fight details section
            weight_class = soup.select_one('i.b-fight-details__fight-title')
            fight_data['weight_class'] = weight_class.text.strip() if weight_class else None
            
            # Get fighter nicknames
            nicknames = soup.select('p.b-fight-details__person-title')
            fight_data['fighter1_nickname'] = nicknames[0].text.strip() if len(nicknames) > 0 else None
            fight_data['fighter2_nickname'] = nicknames[1].text.strip() if len(nicknames) > 1 else None
            
            # Get fighter links
            fighter_links = soup.select('h3.b-fight-details__person-name a')
            fight_data['fighter1_link'] = fighter_links[0]['href'] if len(fighter_links) > 0 else None
            fight_data['fighter2_link'] = fighter_links[1]['href'] if len(fighter_links) > 1 else None
            
            # Get all stat rows
            stat_rows = soup.select('tr.b-fight-details__table-row-preview')
            
            for row in stat_rows:
                # Get stat name
                stat_name = row.select_one('td.l-page_align_left p.b-fight-details__table-text')
                if stat_name:
                    stat_name = stat_name.text.strip().lower().replace(' ', '_').replace('.', '')
                    
                    # Get values for both fighters
                    values = row.select('td:not(.l-page_align_left) p.b-fight-details__table-text')
                    if len(values) >= 2:
                        # Clean and store values
                        fighter1_value = values[0].text.strip()
                        fighter2_value = values[1].text.strip()
                        
                        fight_data[f'fighter1_{stat_name}'] = fighter1_value
                        fight_data[f'fighter2_{stat_name}'] = fighter2_value
            
            detailed_fights.append(fight_data)
            time.sleep(0.1)  # Be nice to the server
            
        except Exception as e:
            print(f"Error processing fight {row['fight_link']}: {e}")
            continue
    
    # Create DataFrame from all fights
    detailed_df = pd.DataFrame(detailed_fights)
    
    if detailed_df.empty:
        print("No new fight details to add")
        return pd.DataFrame()
    
    # Organize columns
    base_cols = ['event_name', 'event_date', 'event_location', 'event_link', 
                 'fight_link', 'fighter1', 'fighter2', 'weight_class']
    
    # Get all other columns and sort them
    other_cols = [col for col in detailed_df.columns if col not in base_cols]
    sorted_cols = base_cols + sorted(other_cols)
    
    return detailed_df[sorted_cols]

def debug_dataframe(df, label="DataFrame"):
    """
    Print debug information about a DataFrame
    """
    if df is None or df.empty:
        print(f"{label} is empty")
        return
        
    print(f"{label} info:")
    print(f"  - Shape: {df.shape}")
    print(f"  - Columns: {df.columns.tolist()}")
    if 'event_link' in df.columns:
        print(f"  - Unique events: {len(df['event_link'].unique())}")
    if 'fight_link' in df.columns:
        print(f"  - Unique fights: {len(df['fight_link'].unique())}")
    if 'event_name' in df.columns:
        print(f"  - Event names: {df['event_name'].unique().tolist()[:3]} (showing first 3)")

def save_data(df: pd.DataFrame, output_file: str) -> None:
    """
    Save DataFrame to Excel file, merging with existing data if file exists
    
    Parameters:
    df (pd.DataFrame): DataFrame to save
    output_file (str): Path to output file
    """
    if df.empty:
        print(f"No new data to save to {output_file}")
        return
    
    # Debug the new data
    debug_dataframe(df, "New data to save")
        
    if os.path.exists(output_file):
        try:
            # Load existing data
            existing_data = pd.read_excel(output_file)
            
            # Debug the existing data
            debug_dataframe(existing_data, "Existing data")
            
            # Check for duplicates before merging
            if 'fight_link' in df.columns and 'fight_link' in existing_data.columns:
                new_links = set(df['fight_link'].unique())
                existing_links = set(existing_data['fight_link'].unique())
                overlap = new_links.intersection(existing_links)
                if overlap:
                    print(f"Warning: Found {len(overlap)} overlapping fight links that may cause duplicates")
                    print(f"First few overlapping links: {list(overlap)[:3]}")
            
            # Concatenate with new data
            combined_data = pd.concat([existing_data, df], ignore_index=True)
            
            # Remove duplicates if they exist
            if 'fight_link' in combined_data.columns:
                before_count = len(combined_data)
                combined_data = combined_data.drop_duplicates(subset=['fight_link'])
                after_count = len(combined_data)
                if before_count > after_count:
                    print(f"Removed {before_count - after_count} duplicate rows")
            
            print(f"Combined {len(existing_data)} existing rows with {len(df)} new rows")
            
            # Save the combined data
            combined_data.to_excel(output_file, index=False)
            print(f"Data saved to {output_file}")
            
            # Display summary
            if 'fight_link' in combined_data.columns:
                print(f"Total: {len(combined_data)} rows from {len(combined_data['fight_link'].unique())} fights")
            elif 'event_name' in combined_data.columns:
                print(f"Total: {len(combined_data)} rows from {len(combined_data['event_name'].unique())} events")
        except Exception as e:
            print(f"Error saving data: {e}")
            import traceback
            traceback.print_exc()
    else:
        # Just save the new data if no existing file
        df.to_excel(output_file, index=False)
        print(f"Data saved to {output_file}")
        
        # Display summary
        if 'fight_link' in df.columns:
            print(f"Total: {len(df)} rows from {len(df['fight_link'].unique())} fights")
        elif 'event_name' in df.columns:
            print(f"Total: {len(df)} rows from {len(df['event_name'].unique())} events")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scrape UFC fights data')
    parser.add_argument('--events', type=int, help='Number of events to scrape (default: all events)')
    parser.add_argument('--previous', action='store_true', help='Scrape previous events')
    parser.add_argument('--upcoming', action='store_true', help='Scrape upcoming events')
    args = parser.parse_args()
    
    # Define output file paths - ensure UFC directory exists
    output_dir = 'data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    previous_events_file = os.path.join(output_dir, 'ufc_events.xlsx')
    upcoming_events_file = os.path.join(output_dir, 'ufc_upcoming_events.xlsx')
    
    print(f"Previous events will be saved to: {previous_events_file}")
    print(f"Upcoming events will be saved to: {upcoming_events_file}")
    
    # If no specific action is requested, do both
    if not args.previous and not args.upcoming:
        args.previous = True
        args.upcoming = True
    
    # Process previous events
    if args.previous:
        # Get already processed events and fights
        processed_events = get_already_processed_events(previous_events_file)
        processed_fights = get_already_processed_fights(previous_events_file)
        
        print(f"Starting to scrape previous events (skipping {len(processed_events)} already processed events)")
        
        # Scrape previous events
        df = scrape_ufc_fights(
            num_events=args.events,
            processed_events=processed_events,
            processed_fights=processed_fights
        )
        
        if not df.empty:
            print(f"Found {len(df)} new fights to add to {previous_events_file}")
            # Save data
            save_data(df, previous_events_file)
        else:
            print(f"No new fights found to add to {previous_events_file}")
    
    # Process upcoming events
    if args.upcoming:
        # Get already processed upcoming events
        processed_event_names = get_already_processed_upcoming_events(upcoming_events_file)
        processed_fights = get_already_processed_fights(upcoming_events_file)
        
        print(f"Starting to scrape upcoming events (skipping {len(processed_event_names)} already processed events)")
        
        # Scrape upcoming events
        df = scrape_upcoming(processed_event_names=processed_event_names)
        
        if not df.empty:
            print(f"Found {len(df)} new upcoming fights to process")
            # Scrape detailed fight information
            df_detailed = scrape_fight_details(df, processed_fights=processed_fights)
            
            # Save data
            save_data(df_detailed, upcoming_events_file)
        else:
            print("No new upcoming events found")

if __name__ == "__main__":
    main()
