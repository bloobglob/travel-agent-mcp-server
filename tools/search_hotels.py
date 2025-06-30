from amadeus import Client, ResponseError
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
amadeus = Client()

def convert_hotel_offers_to_text(hotel_data):
    """
    Convert hotel offers JSON data to readable text format.
    
    Args:
        hotel_data: List of hotel offer dictionaries or single dictionary
    
    Returns:
        str: Formatted text representation of hotel offers
    """
    # Handle single dictionary input
    if isinstance(hotel_data, dict):
        hotel_data = [hotel_data]
    
    output_lines = []
    
    if not hotel_data:
        hotel_data = [{'hotel': {'name': 'No Hotels Found', 'cityCode': 'N/A'}, 'available': False}]
    
    for i, hotel_offer in enumerate(hotel_data):
        output_lines.append(f"=== HOTEL OPTION {i+1} ===\n")
        
        # Hotel Information
        hotel = hotel_offer.get('hotel', {})
        output_lines.append(f"HOTEL: {hotel.get('name', 'N/A')}")
        output_lines.append(f"LOCATION: {hotel.get('cityCode', 'N/A')}")
        
        # Availability
        available = hotel_offer.get('available', False)
        status = "Available" if available else "Not Available"
        output_lines.append(f"STATUS: {status}")
        
        if not available:
            output_lines.append("\n" + "="*50 + "\n")
            continue
        
        # Process offers
        offers = hotel_offer.get('offers', [])
        
        for j, offer in enumerate(offers, 1):
            if len(offers) > 1:
                output_lines.append(f"\n--- Offer {j} ---")
            
            # Dates
            check_in = offer.get('checkInDate', 'N/A')
            check_out = offer.get('checkOutDate', 'N/A')
            output_lines.append(f"CHECK-IN: {format_date(check_in)}")
            output_lines.append(f"CHECK-OUT: {format_date(check_out)}")
            
            # Calculate nights
            if check_in != 'N/A' and check_out != 'N/A':
                try:
                    nights = (datetime.strptime(check_out, '%Y-%m-%d') - 
                             datetime.strptime(check_in, '%Y-%m-%d')).days
                    output_lines.append(f"NIGHTS: {nights}")
                except:
                    pass
            
            # Room Information
            room = offer.get('room', {})
            room_desc = room.get('description', {}).get('text', '')
            type_est = room.get('typeEstimated', {})
            
            output_lines.append(f"ROOM TYPE: {type_est.get('category', 'Standard Room').replace('_', ' ').title()}")
            output_lines.append(f"BED: {type_est.get('beds', 1)} {type_est.get('bedType', 'Bed').title()}")
            
            # Extract room size from description if available
            if 'sqft' in room_desc or 'sqm' in room_desc:
                size_info = extract_room_size(room_desc)
                if size_info:
                    output_lines.append(f"ROOM SIZE: {size_info}")
            
            # Guests
            guests = offer.get('guests', {})
            adults = guests.get('adults', 0)
            children = guests.get('children', 0)
            guest_info = f"{adults} Adult(s)"
            if children > 0:
                guest_info += f", {children} Child(ren)"
            output_lines.append(f"GUESTS: {guest_info}")
            
            # Pricing
            price = offer.get('price', {})
            currency = price.get('currency', 'USD')
            total = price.get('total', '0')
            base = price.get('base', '0')
            
            output_lines.append(f"TOTAL PRICE: {currency} ${total}")
            output_lines.append(f"BASE PRICE: {currency} ${base}")
            
            # Average nightly rate
            variations = price.get('variations', {})
            avg_base = variations.get('average', {}).get('base', '0')
            if avg_base != '0':
                output_lines.append(f"AVG PER NIGHT: {currency} ${avg_base}")
            
            # Cancellation Policy
            policies = offer.get('policies', {})
            cancellations = policies.get('cancellations', [])
            refundable = policies.get('refundable', {})
            
            if cancellations:
                cancel_policy = cancellations[0]
                deadline = cancel_policy.get('deadline', '')
                if deadline:
                    formatted_deadline = format_datetime(deadline)
                    output_lines.append(f"CANCELLATION: Free until {formatted_deadline}")
                
                cancel_fee = cancel_policy.get('amount', '0')
                if cancel_fee != '0':
                    output_lines.append(f"CANCELLATION FEE: {currency} ${cancel_fee}")
            
            # Refund status
            refund_type = refundable.get('cancellationRefund', '')
            if 'REFUNDABLE' in refund_type:
                output_lines.append("REFUNDABLE: Yes (with conditions)")
            elif 'NON_REFUNDABLE' in refund_type:
                output_lines.append("REFUNDABLE: No")
        
        output_lines.append("\n" + "="*50 + "\n")
    
    return "\n".join(output_lines)

def format_date(date_str):
    """Format date string to more readable format"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%B %d, %Y')
    except:
        return date_str

def format_datetime(datetime_str):
    """Format datetime string to more readable format"""
    try:
        # Handle timezone format
        if 'T' in datetime_str:
            dt_part = datetime_str.split('T')[0]
            time_part = datetime_str.split('T')[1].split('-')[0].split('+')[0]
            date_obj = datetime.strptime(dt_part, '%Y-%m-%d')
            time_obj = datetime.strptime(time_part, '%H:%M:%S')
            return f"{date_obj.strftime('%B %d, %Y')} at {time_obj.strftime('%I:%M %p')}"
        return datetime_str
    except:
        return datetime_str

def extract_room_size(description):
    """Extract room size information from description"""
    import re
    size_pattern = r'(\d+)sqft/(\d+)sqm'
    match = re.search(size_pattern, description)
    if match:
        sqft, sqm = match.groups()
        return f"{sqft} sq ft ({sqm} sq m)"
    return None

def list_hotels(city_code):
    """
    List hotels in a city using Amadeus hotel search.
    """
    response = amadeus.get('/v1/reference-data/locations/hotels/by-city', cityCode=city_code)
    hotels = response.data
    return hotels[0:20]

def search_hotels(city_code, check_in, check_out, adults=1):
    """
    List hotels and fetch offers for each.
    """
    hotels = list_hotels(city_code)
    hotel_ids = [hotel['hotelId'] for hotel in hotels]
    print(hotel_ids, adults, check_in, check_out)
    response = amadeus.shopping.hotel_offers_search.get(hotelIds=','.join(hotel_ids), adults=adults, checkInDate=check_in, checkOutDate=check_out, roomQuantity=1)
    return response.data

if __name__ == "__main__":
    print(convert_hotel_offers_to_text(search_hotels("NYC", "2025-07-01", "2025-07-05", 2)))  # Example usage
    # city_code = "NYC"
    # check_in = "2025-07-01"
    # check_out = "2025-07-05"
    # adults = 2
    # hotels_with_offers = search_hotels(city_code, check_in, check_out, adults)
    # for entry in hotels_with_offers:
    #     print(f"Hotel: {entry['hotel']['name']}")
    #     print(f"Offers: {entry['offers']}\n")