from amadeus import Client, Location, ResponseError
from dotenv import load_dotenv
import os
import pprint
import json
import pickle
from datetime import datetime

load_dotenv()

amadeus = Client()

def parse_flight_data(flight_data):
    """
    Parse flight offer JSON data and convert to simplified flight details format.
    
    Args:
        flight_json_string (str): JSON string containing flight offers data
        
    Returns:
        list: Array of dictionaries with formatted flight details
    """
    
    def parse_duration(duration_str):
        """Convert ISO 8601 duration to human readable format"""
        if not duration_str:
            return "N/A"
        
        # Remove PT prefix and parse
        duration_str = duration_str.replace('PT', '')
        hours = 0
        minutes = 0
        
        if 'H' in duration_str:
            hours_part = duration_str.split('H')[0]
            hours = int(hours_part)
            duration_str = duration_str.split('H')[1] if 'H' in duration_str else duration_str
        
        if 'M' in duration_str:
            minutes_part = duration_str.replace('M', '')
            if minutes_part:
                minutes = int(minutes_part)
        
        return f"{hours}h {minutes}m"
    
    def calculate_layover(arrival_time, departure_time):
        """Calculate layover time between flights"""
        try:
            arrival = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
            departure = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            layover = departure - arrival
            
            hours = layover.seconds // 3600
            minutes = (layover.seconds % 3600) // 60
            
            return f"{hours}h {minutes}m"
        except:
            return "N/A"
    
    def format_datetime(dt_str):
        """Format datetime string to readable format"""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return dt_str
    
    try:
        # Parse JSON data
        # flight_data = json.loads(flight_json_string)
        
        # Ensure we have a list of flight offers
        if not isinstance(flight_data, list):
            flight_data = [flight_data]
        
        parsed_flights = []
        
        for flight_offer in flight_data:
            # Extract basic flight information
            flight_id = flight_offer.get('id', 'N/A')
            price_info = flight_offer.get('price', {})
            total_price = price_info.get('total', 'N/A')
            currency = price_info.get('currency', 'N/A')
            
            # Get first traveler pricing for cabin and baggage info
            traveler_pricing = flight_offer.get('travelerPricings', [{}])[0]
            fare_details = traveler_pricing.get('fareDetailsBySegment', [])
            
            # Extract cabin class and baggage from first segment
            cabin_class = fare_details[0].get('cabin', 'N/A') if fare_details else 'N/A'
            checked_bags = fare_details[0].get('includedCheckedBags', {}).get('quantity', 0) if fare_details else 0
            cabin_bags = fare_details[0].get('includedCabinBags', {}).get('quantity', 0) if fare_details else 0
            
            baggage_allowance = f"Checked: {checked_bags}, Cabin: {cabin_bags}"
            
            # Process all itineraries (outbound and return) as one combined flight
            itineraries = flight_offer.get('itineraries', [])
            
            # Combine all segments from all itineraries
            all_detailed_itinerary = []
            all_airline_info = []
            all_aircraft_types = []
            total_flight_duration = []
            
            for itinerary_idx, itinerary in enumerate(itineraries):
                segments = itinerary.get('segments', [])
                itinerary_duration = parse_duration(itinerary.get('duration', ''))
                total_flight_duration.append(itinerary_duration)
                
                # Add itinerary header
                itinerary_type = 'Outbound' if itinerary_idx == 0 else 'Return'
                all_detailed_itinerary.append(f"--- {itinerary_type} ({itinerary_duration}) ---")
                
                # Build detailed itinerary with layovers for this itinerary
                for segment_idx, segment in enumerate(segments):
                    # Extract segment details
                    departure = segment.get('departure', {})
                    arrival = segment.get('arrival', {})
                    carrier_code = segment.get('carrierCode', 'N/A')
                    flight_number = segment.get('number', 'N/A')
                    aircraft_code = segment.get('aircraft', {}).get('code', 'N/A')
                    segment_duration = parse_duration(segment.get('duration', ''))
                    
                    # Format segment information
                    dep_airport = departure.get('iataCode', 'N/A')
                    dep_terminal = departure.get('terminal', '')
                    dep_time = format_datetime(departure.get('at', ''))
                    
                    arr_airport = arrival.get('iataCode', 'N/A')
                    arr_terminal = arrival.get('terminal', '')
                    arr_time = format_datetime(arrival.get('at', ''))
                    
                    # Build segment string
                    segment_info = f"{dep_airport}"
                    if dep_terminal:
                        segment_info += f" (T{dep_terminal})"
                    segment_info += f" {dep_time} -> {arr_airport}"
                    if arr_terminal:
                        segment_info += f" (T{arr_terminal})"
                    segment_info += f" {arr_time} | {carrier_code}{flight_number} | {segment_duration}"
                    
                    all_detailed_itinerary.append(segment_info)
                    all_airline_info.append(f"{carrier_code}{flight_number}")
                    all_aircraft_types.append(aircraft_code)
                    
                    # Calculate layover time if not the last segment in this itinerary
                    if segment_idx < len(segments) - 1:
                        next_segment = segments[segment_idx + 1]
                        layover_time = calculate_layover(
                            arrival.get('at', ''),
                            next_segment.get('departure', {}).get('at', '')
                        )
                        all_detailed_itinerary.append(f"Layover: {layover_time}")
                
                # Add spacing between itineraries (except after the last one)
                if itinerary_idx < len(itineraries) - 1:
                    all_detailed_itinerary.append("")
            
            # Create single flight record combining all itineraries
            flight_record = {
                'flight_id': flight_id,
                'total_price': total_price,
                'currency': currency,
                'flight_duration': ' + '.join(total_flight_duration),
                'airline_flight_numbers': ', '.join(all_airline_info),
                'aircraft_types': ', '.join(set(all_aircraft_types)),  # Remove duplicates
                'cabin_class': cabin_class,
                'baggage_allowance': baggage_allowance,
                'detailed_itinerary': all_detailed_itinerary
            }
            
            parsed_flights.append(flight_record)
        
        return parsed_flights
        
    except json.JSONDecodeError as e:
        return [{'error': f'Invalid JSON format: {str(e)}'}]
    except Exception as e:
        return [{'error': f'Error parsing flight data: {str(e)}'}]


# Example usage function
def flight_summary(flights):
    """Return a formatted summary of parsed flights"""
    ret = ""
    for i, flight in enumerate(flights, 1):
        if 'error' in flight:
            print(f"Error: {flight['error']}")
            continue
            
        ret += (f"\n # --- Flight Option {i} ---\n")
        ret += (f"Flight ID: {flight['flight_id']}\n")
        ret += (f"Price: {flight['total_price']} {flight['currency']}\n")
        ret += (f"Duration: {flight['flight_duration']}\n")
        ret += (f"Airlines/Flights: {flight['airline_flight_numbers']}\n")
        ret += (f"Aircraft: {flight['aircraft_types']}\n")
        ret += (f"Cabin: {flight['cabin_class']}\n")
        ret += (f"Baggage: {flight['baggage_allowance']}\n")
        ret += (" ## Itinerary:\n")
        for segment in flight['detailed_itinerary']:
            if segment.startswith('---'):
                ret += (f"  ### {segment}\n")
            elif segment.startswith('Layover:'):
                ret += (f"    {segment}\n")
            elif segment == "":
                ret += ("\n")
            else:
                ret += (f"    - {segment}\n")
    return ret

def prune_flight_offers(flight_data):
    """
    Prunes flight offer data to include only customer-relevant information for decision making.
    Keeps: id, route, times, duration, price, cabin class, airline, aircraft, baggage
    Removes: technical fields, fare codes, segment IDs, etc.
    """
    
    pruned_offers = []
    
    for offer in flight_data:
        pruned_offer = {
            'id': offer['id'],
            'price': {
                'total': offer['price']['total'],
                'currency': offer['price']['currency']
            },
            'lastTicketingDate': offer['lastTicketingDate'],
            'numberOfBookableSeats': offer['numberOfBookableSeats'],
            'itineraries': []
        }
        
        # Process each itinerary
        for itinerary in offer['itineraries']:
            pruned_itinerary = {
                'duration': itinerary['duration'],
                'segments': []
            }
            
            # Process each segment
            for segment in itinerary['segments']:
                pruned_segment = {
                    'departure': {
                        'airport': segment['departure']['iataCode'],
                        'time': segment['departure']['at']
                    },
                    'arrival': {
                        'airport': segment['arrival']['iataCode'],
                        'time': segment['arrival']['at']
                    },
                    'airline': segment['carrierCode'],
                    'flightNumber': segment['number'],
                    'aircraft': segment['aircraft']['code'],
                    'duration': segment['duration'],
                    'stops': segment['numberOfStops']
                }
                pruned_itinerary['segments'].append(pruned_segment)
            
            pruned_offer['itineraries'].append(pruned_itinerary)
        
        # Add cabin class and baggage info from traveler pricing
        if offer['travelerPricings']:
            traveler = offer['travelerPricings'][0]  # Assuming single traveler
            pruned_offer['cabin'] = traveler['fareDetailsBySegment'][0]['cabin']
            pruned_offer['includedBags'] = traveler['fareDetailsBySegment'][0]['includedCheckedBags']['quantity']
        
        pruned_offers.append(pruned_offer)
    
    return pruned_offers

def search_flights(orig_location_code: str, dest_location_code: str, dest2_location_code: str,
                   orig_date: str, dept_date: str,
                   infant_count: int, child_count: int, adult_count: int):
    travelers = []
    id = 1
    for _ in range(adult_count):
        travelers.append({'id': str(id), 'travelerType': 'ADULT'})
        id += 1
    for _ in range(child_count):
        travelers.append({'id': str(id), 'travelerType': 'CHILD'})
        id += 1
    for i in range(infant_count):
        travelers.append({'id': str(id), 'travelerType': 'HELD_INFANT', 'associatedAdultId': str(i + 1)})
        id += 1
    body =  {
                'currencyCode': 'USD',
                'originDestinations': [{'id': '1',
                                        'originLocationCode': orig_location_code,
                                        'destinationLocationCode': dest_location_code,
                                        'departureDateTimeRange': {'date': orig_date,
                                                                    'time': '00:00:00'}},
                                        {'id': '2',
                                        'originLocationCode': dest2_location_code,
                                        'destinationLocationCode': orig_location_code,
                                        'departureDateTimeRange': {'date': dept_date,
                                                                    'time': '00:00:00'}}],
                'travelers': travelers,
                'sources': ['GDS'],
                'searchCriteria': {'maxFlightOffers': 4}
            }
    try:
        response = amadeus.shopping.flight_offers_search.post(body)
        # with open('test.json', 'w') as f:
        #     f.write(response.data)
        # flight_offers = prune_flight_offers(response.data)
        # with open('flight_offers.pkl', 'wb') as f:
        #     pickle.dump(flight_offers, f)
        # return flight_offers
        return flight_summary(parse_flight_data(response.data))
    except ResponseError as error:
        raise error
    
if __name__ == "__main__":
    print(search_flights('LAX', 'TPE', 'TPE', '2025-07-01', '2025-07-07', 0, 0, 2))
    # pfd = parse_flight_data(search_flights('NYC', 'LON', 'LON', '2025-07-01', '2025-07-08', 0, 1, 2))
    # print(flight_summary(pfd))
    # with open('test.json', 'w') as f:
    #     f.write(str(pfd))