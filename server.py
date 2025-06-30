from fastmcp import FastMCP
import os
import uvicorn
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route
from tools.search_flights import search_flights as _search_flights
from tools.google_search import async_google_search as _async_google_search
from tools.search_hotels import search_hotels as _search_hotels
from tools.search_hotels import convert_hotel_offers_to_text as _convert_hotel_offers_to_text
from tools.create_pdf import create_trip_pdf as _create_trip_pdf

mcp = FastMCP('travel-agent-mcp-server', json_response=True, stateless_http=True)

@mcp.tool
def search_flights(orig_location_code: str, dest_location_code: str, dest2_location_code: str,
                   orig_date: str, dept_date: str,
                   infant_count: int, child_count: int, adult_count: int) -> str:
    print('search flights called')
    return _search_flights(orig_location_code, dest_location_code, dest2_location_code,
                                orig_date, dept_date,
                                infant_count, child_count, adult_count)
    
    
@mcp.tool
async def google_search(gs_query: str) -> str:
    """Google searches the prompt"""
    return await _async_google_search(gs_query)

@mcp.tool
def search_hotels(city_codes_str: str, orig_date: str, dest_dates_str: str, adults: int) -> str:
    """
    Search hotels in a city using Amadeus hotel search.
    """
    print('search hotels called')
    city_codes = city_codes_str.split(',')
    dest_dates = dest_dates_str.split(',')
    ret = ''
    for i, city_code in enumerate(city_codes):
        check_in = orig_date if i == 0 else dest_dates[i - 1]
        check_out = dest_dates[i]
        hotels_with_offers = _search_hotels(city_code, check_in, check_out, adults)
        ret += f"# Hotels in {city_code} from {check_in} to {check_out}:\n"
        ret += _convert_hotel_offers_to_text(hotels_with_offers) + "\n\n"
    return ret

@mcp.tool
def create_trip_pdf(
    orig_city: str,
    orig_date: str,
    dest_cities: str,
    dest_dates: str,
    flight: str,
    hotels: str,
    itinerary: str
):
    return _create_trip_pdf(
        orig_city=orig_city,
        orig_date=orig_date,
        dest_cities=dest_cities,
        dest_dates=dest_dates,
        flight=flight,
        hotels=hotels,
        itinerary=itinerary
    )

app = mcp.http_app()

async def download_file(request):
    filename = request.path_params['filename']
    file_path = f'output/{filename}'
    
    if not os.path.exists(file_path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    
    return FileResponse(
        file_path,
        media_type='application/pdf',
        filename=filename
    )
    
download_route = Route('/download/{filename}', download_file, methods=['GET'])
app.routes.append(download_route)

def main():
    uvicorn.run(app, host='0.0.0.0', port=8000)

if __name__ == "__main__":
    main()