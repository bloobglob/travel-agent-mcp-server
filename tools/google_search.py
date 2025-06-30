from playwright.async_api import async_playwright
import asyncio
import json
from typing import List, Dict, Any
from langchain.agents import Tool
import logging
import os

logger = logging.getLogger(__name__)

async def async_google_search(query: str, max_retries: int = 2) -> str:
    """
    Enhanced Google search with better debugging
    """
    for attempt in range(max_retries):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Anti-detection script
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    delete navigator.webdriver;
                """)
                
                print(f"🔍 Attempt {attempt + 1}: Searching for '{query}'")
                
                # First visit Google homepage
                await page.goto('https://www.google.com', timeout=15000)
                await page.wait_for_timeout(2000)
                
                # Execute search
                search_url = f"https://www.google.com/search?q={query}&hl=en&num=10"
                print(f"📡 Navigating to: {search_url}")
                
                response = await page.goto(search_url, wait_until='networkidle', timeout=15000)
                print(f"📄 Response status: {response.status}")
                
                # Wait for page to load
                await page.wait_for_timeout(3000)
                
                # Screenshot for debugging
                screenshot_path = f'debug_search_{attempt}.png'
                await page.screenshot(path=screenshot_path)
                print(f"📸 Screenshot saved: {screenshot_path}")
                
                # Check page title and basic information
                page_title = await page.title()
                page_url = page.url
                print(f"📋 Page title: {page_title}")
                print(f"🌐 Current URL: {page_url}")
                
                # Check if redirected or showing verification page
                if "sorry" in page_title.lower() or "captcha" in page_title.lower():
                    print("⚠️ Google CAPTCHA or verification detected!")
                    await browser.close()
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    return "Google verification required. Please try again later."
                
                # Try multiple selector strategies
                selectors_to_try = [
                    "div.g",                   # Traditional selector
                    "div.MjjYud",              # New main selector
                    "div.kvH3mc",              # Alternative selector
                    "[data-ved]",              # Attribute-based selector
                    "div[data-hveid]",         # Data attribute selector
                    "div:has(h3)",             # Div containing h3
                    ".tF2Cxc",                 # Another possible selector
                ]
                
                search_results = []
                successful_selector = None
                
                for selector in selectors_to_try:
                    try:
                        elements = await page.locator(selector).all()
                        if elements and len(elements) > 0:
                            # Filter out elements that are obviously not search results
                            valid_elements = []
                            for element in elements:
                                try:
                                    # Check if element contains title element
                                    has_title = await element.locator("h3, h1, h2").count() > 0
                                    has_link = await element.locator("a").count() > 0
                                    if has_title or has_link:
                                        valid_elements.append(element)
                                except:
                                    continue
                            
                            if valid_elements:
                                search_results = valid_elements
                                successful_selector = selector
                                print(f"✅ Found {len(search_results)} results with selector: {selector}")
                                break
                    except Exception as e:
                        print(f"❌ Selector '{selector}' failed: {e}")
                        continue
                
                if not search_results:
                    # Get page content for debugging
                    page_content = await page.content()
                    print(f"📄 Page content length: {len(page_content)}")
                    print(f"📄 Page content preview:\n{page_content[:1000]}...")
                    
                    # Save full page content to file
                    with open(f'debug_page_content_{attempt}.html', 'w', encoding='utf-8') as f:
                        f.write(page_content)
                    print(f"💾 Full page content saved to debug_page_content_{attempt}.html")
                    
                    await browser.close()
                    if attempt < max_retries - 1:
                        print(f"🔄 No results found, retrying in 5 seconds...")
                        await asyncio.sleep(5)
                        continue
                    return "No search results found after trying multiple selectors."
                
                # Extract search results
                results = []
                print(f"🔍 Extracting data from {len(search_results)} results...")
                
                for i, result in enumerate(search_results[:5]):
                    try:
                        print(f"📝 Processing result {i+1}...")
                        
                        # Extract title
                        title = ""
                        title_selectors = ["h3", "h1", "h2", "[role='heading']"]
                        for title_sel in title_selectors:
                            try:
                                title_element = result.locator(title_sel).first
                                if await title_element.count() > 0:
                                    title = await title_element.inner_text()
                                    if title and title.strip():
                                        break
                            except:
                                continue
                        
                        # Extract link
                        link = ""
                        try:
                            link_element = result.locator("a").first
                            if await link_element.count() > 0:
                                link = await link_element.get_attribute("href")
                                # Clean Google redirect links
                                if link and link.startswith('/url?q='):
                                    link = link.split('/url?q=')[1].split('&')[0]
                        except:
                            pass
                        
                        # Extract description
                        description = ""
                        desc_selectors = [
                            ".VwiC3b", ".s3v9rd", ".hgKElc", ".IsZvec",
                            "span:not(:has(a))", "div:not(:has(h3)):not(:has(a))"
                        ]
                        for desc_sel in desc_selectors:
                            try:
                                desc_element = result.locator(desc_sel).first
                                if await desc_element.count() > 0:
                                    desc_text = await desc_element.inner_text()
                                    if desc_text and len(desc_text.strip()) > 15:
                                        description = desc_text[:300] + "..." if len(desc_text) > 300 else desc_text
                                        break
                            except:
                                continue
                        
                        # Only add valid results
                        if title and title.strip() and len(title.strip()) > 3:
                            result_data = {
                                "title": title.strip(),
                                "url": link or "No URL available",
                                "description": description or "No description available"
                            }
                            results.append(result_data)
                            print(f"✅ Result {i+1}: {title[:50]}...")
                        else:
                            print(f"⚠️ Result {i+1}: Invalid or empty title")
                            
                    except Exception as e:
                        print(f"❌ Error extracting result {i+1}: {e}")
                        continue
                
                await browser.close()
                
                if not results:
                    if attempt < max_retries - 1:
                        print(f"🔄 No valid results extracted on attempt {attempt + 1}, retrying...")
                        await asyncio.sleep(5)
                        continue
                    return "No valid search results could be extracted after all attempts."
                
                # Format final results
                print(f"🎉 Successfully extracted {len(results)} results!")
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. {result['title']}\n"
                        f"URL: {result['url']}\n"
                        f"Description: {result['description']}"
                    )
                
                final_result = "🔍 Google Search Results:\n\n" + "\n\n".join(formatted_results)
                print(f"📤 Returning {len(results)} results")
                return final_result
                
        except Exception as e:
            error_msg = f"Search failed on attempt {attempt + 1}: {str(e)}"
            print(f"❌ {error_msg}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue
            else:
                return f"Search failed after all attempts: {str(e)}"
    
    return "Search failed after all retries."

def google_search(query: str) -> str:
    """
    Synchronous wrapper with error handling
    """
    try:
        print(f"🚀 Starting Google search for: '{query}'")
        result = asyncio.run(async_google_search(query))
        print(f"✅ Search completed")
        return result
    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg

# Create Langchain tool
google_search_tool = Tool(
    name="GoogleSearch",
    description="Google search tool that returns search results with titles, URLs, and descriptions. Input should be a search query string.",
    func=google_search
)

__all__ = ["google_search", "async_google_search", "google_search_tool"]