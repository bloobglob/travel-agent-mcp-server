from fpdf import FPDF
from urllib.parse import unquote

def create_trip_pdf(
    orig_city: str,
    orig_date: str,
    dest_cities: str,
    dest_dates: str,
    flight: str,
    hotels: str,
    itinerary: str,
    output_path: str = "output/trip_summary.pdf"
):
    flight = unquote(flight)
    hotels = unquote(hotels)
    itinerary = unquote(itinerary)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Your Travel Summary", ln=True, align="C")
    pdf.ln(10)

    # Section: Origin
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Origin", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, f"City: {orig_city}\nDate: {orig_date}")
    pdf.ln(5)

    # Section: Destinations
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Destinations", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, f"Cities: {dest_cities}\nDates: {dest_dates}")
    pdf.ln(5)

    # Section: Flight
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Flight Details", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, flight)
    pdf.ln(5)

    # Section: Hotels
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Hotel Choices", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, hotels)
    pdf.ln(5)

    # Section: Itinerary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Itinerary", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, itinerary)
    pdf.ln(5)

    pdf.output(output_path)

# Example usage:
# if __name__ == "__main__":
#     create_trip_pdf(
#         orig_city="San Francisco",
#         orig_date="2025-07-01",
#         dest_cities="Paris, Rome",
#         dest_dates="2025-07-02, 2025-07-05",
#         flight="Flight: UA123, SFO to CDG, 2025-07-01\nFlight: AF456, CDG to FCO, 2025-07-05",
#         hotels="Paris: Hotel Le Meurice, 2025-07-02 to 2025-07-05\nRome: Hotel Eden, 2025-07-05 to 2025-07-10",
#         itinerary="Day 1: Arrive in Paris\nDay 2: Louvre\nDay 3: Eiffel Tower\nDay 4: Fly to Rome\nDay 5: Colosseum"
#     )