# from web_scraper.core.scraper import WebScraper
# from web_scraper.config.settings import WebScrapingConfig
# from web_scraper.core.models import ElementInfo, ElementSignature
# # from web_scraper.exceptions.scraper_exceptions import InvalidURLError, PageTooLargeError
# import requests


# def main():
#     """Example usage demonstrating Sprint 1 functionality"""

#     # Create scraper with custom config
#     config = WebScrapingConfig(
#         timeout=20,
#         max_retries=2,
#         exclude_tags=['script', 'style', 'meta']
#     )

#     scraper = WebScraper(config)

#     # Example URLs for testing (replace with actual URLs)
#     test_urls = [
#         "https://httpbin.org/html",  # Simple test page
#         "https://example.com"        # Basic example page
#     ]

#     for url in test_urls:
#         try:
#             print(f"\n=== Analyzing {url} ===")

#             # Fetch and parse the page
#             doc = scraper.fetch_page(url)
#             print(f"Successfully fetched: {doc.response_info['final_url']}")
#             print(f"Status: {doc.response_info['status_code']}")
#             print(f"Content length: {doc.response_info['content_length']} bytes")

#             # Extract all elements
#             elements = doc.extract_all_elements()
#             print(f"Extracted {len(elements)} elements")

#             # Show document statistics
#             stats = doc.get_document_stats()
#             print(f"Document stats: {stats}")

#             # Show first few elements as examples
#             print("\nFirst 5 elements:")
#             for i, element in enumerate(elements[:5]):
#                 print(f"{i+1}. {element.tag} "
#                       f"(classes: {element.classes}, "
#                       f"depth: {element.depth}, "
#                       f"text: '{element.text[:50]}...' if element.text else 'no text')")

#             # Test signature generation
#             print(f"\nExample signatures:")
#             for element in elements[:3]:
#                 signature = doc.generate_signature(element)
#                 print(f"  {element.tag}: {signature}")

#         except (requests.RequestException, ValueError) as e:
#             print(f"Error processing {url}: {e}")
#         # except (InvalidURLError, PageTooLargeError, requests.RequestException) as e:
#         #    print(f"Error processing {url}: {e}")


# if __name__ == "__main__":
#     main()
#     print("\n=== Sprint 1 Implementation Complete ===")
#     print("Features implemented:")
#     print("✓ Basic HTML fetching with error handling")
#     print("✓ HTML element extraction with attributes")
#     print("✓ Element signature generation")
#     print("✓ Document statistics and analysis")
#     print("✓ Configurable scraping behavior")
#     print("✓ Memory-efficient element processing")


# web_scraper/main.py

import requests # Keep requests for exception handling
import time     # Keep time for delays and timing
from typing import Dict, Any, List
# Import classes and models from your new modular structure
from web_scraper.core.scraper import WebScraper
from web_scraper.config.settings import WebScrapingConfig
from web_scraper.core.models import ElementInfo, ElementSignature, ElementType, PatternInfo
from web_scraper.core.document import ParsedDocument 

# def demo_scraper():
#     """Comprehensive demonstration of Sprint 1 functionality"""
#     print("🚀 Web Scraper Library - Sprint 1 Live Demo")
#     print("=" * 50)

#     # Create scraper
#     # Use the WebScrapingConfig from your new config module
#     config = WebScrapingConfig(timeout=10, max_retries=2)
#     # Instantiate WebScraper from your new core.scraper module
#     scraper = WebScraper(config)

#     # Test URLs - mix of simple and complex pages
#     test_urls = [
#         "https://example.com",  # Simple example page
#         "https://httpbin.org/html",  # HTML test page
#         "http://web.simmons.edu/~grovesd/comm244/notes/week3/html-test-page.html" # CSS test page
#         # Add more URLs here to test different scenarios if needed
#     ]

#     for i, url in enumerate(test_urls, 1):
#         print(f"\n🌐 Test {i}/{len(test_urls)}: Analyzing {url}")
#         print("-" * 60)

#         try:
#             # Fetch the page using your modularized scraper
#             start_time = time.time()
#             doc = scraper.fetch_page(url) # This returns a ParsedDocument object
#             fetch_time = time.time() - start_time

#             print(f"✅ Successfully fetched in {fetch_time:.2f}s")
#             print(f"   Status: {doc.response_info['status_code']}")
#             print(f"   Final URL: {doc.response_info['final_url']}")
#             print(f"   Content Length: {doc.response_info['content_length']:,} bytes")

#             # Extract elements using ParsedDocument's method
#             elements = doc.extract_all_elements()
#             print(f"   Elements extracted: {len(elements)}")

#             # Show document statistics
#             stats = doc.get_document_stats()
#             print(f"\n📊 Document Statistics:")
#             print(f"   Total elements: {stats['total_elements']}")
#             print(f"   Unique tags: {stats['unique_tags']}")
#             print(f"   Max depth: {stats['max_depth']}")
#             print(f"   Avg depth: {stats['avg_depth']:.1f}")
#             print(f"   Elements with classes: {stats['elements_with_classes']}")
#             print(f"   Elements with IDs: {stats['elements_with_ids']}")
#             print(f"   Elements with text: {stats['elements_with_text']}")

#             # Show most common tags
#             print(f"\n🏷️  Most Common Tags:")
#             for tag, count in list(stats['most_common_tags'].items())[:8]:
#                 print(f"   {tag}: {count}")

#             # Show element types distribution
#             print(f"\n🎨 Element Types:")
#             for elem_type, count in stats['element_types'].items():
#                 print(f"   {elem_type.title()}: {count}")

#             # Show sample elements with their properties
#             print(f"\n🔍 Sample Elements (first 8):")
#             for j, element in enumerate(elements[:8]):
#                 # Use doc.generate_signature for consistency as it might internally call helpers
#                 sig = doc.generate_signature(element)
#                 text_preview = element.text[:30] + "..." if len(element.text) > 30 else element.text
#                 classes_str = ".".join(element.classes[:3]) if element.classes else "no-classes"

#                 print(f"   {j+1}. <{element.tag}> "
#                       f"classes=[{classes_str}] "
#                       f"depth={element.depth} "
#                       f"children={element.children_count}")

#                 if element.id:
#                     print(f"      ID: {element.id}")
#                 if element.text:
#                     print(f"      Text: '{text_preview}'")


#                 print(f"      Signature: {sig}")
#                 print(f"      XPath: {element.xpath}")
#                 print()

#             # Preview of pattern detection (Sprint 2 sneak peek)
#             # This method is part of ParsedDocument and will use the ElementSignature and ElementInfo models
#             patterns = doc.find_potential_patterns(min_threshold=2)
#             if patterns:
#                 print(f"🔁 Potential Repeating Patterns Found: {len(patterns)}")
#                 # Iterate through a few patterns for display
#                 for sig, elements_list in list(patterns.items())[:5]:
#                     print(f"   Pattern: {sig} -> {len(elements_list)} occurrences")
#                     if elements_list:
#                         sample_text = elements_list[0].text[:40] + "..." if elements_list[0].text else "no text"
#                         print(f"            Sample: <{elements_list[0].tag}> '{sample_text}'")
#             else:
#                 print("🔁 No obvious repeating patterns detected (threshold=2)")

#         # Catch specific exceptions from the modularized code
#         except (requests.RequestException, ValueError) as e:
#             print(f"❌ Error processing {url}: {e}")
#         except Exception as e: # Catch any other unexpected errors
#             print(f"❌ An unexpected error occurred for {url}: {e}")

#         print("\n" + "="*60)

#     print("\n✨ Sprint 1 Demo Complete!")
#     print("\nFeatures Successfully Demonstrated:")
#     print("✅ HTTP fetching with error handling and timeouts")
#     print("✅ HTML parsing and element extraction")
#     print("✅ Element classification and property extraction")
#     print("✅ Signature generation for element grouping")
#     print("✅ Document statistics and analysis")
#     print("✅ XPath generation for element location")
#     print("✅ Memory-efficient processing")
#     print("✅ Preview of pattern detection capabilities")

#     print("\n🚀 Ready for Sprint 2: Pattern Detection & Analysis!")


# if __name__ == "__main__":
#     demo_scraper()


def demo_scraper():
    """
    Demonstrates the capabilities of the Web Scraper Library (Sprint 1 Features).
    """
    print("🚀 Web Scraper Library - Sprint 1 Live Demo")
    print("==================================================\n")

    config = WebScrapingConfig()
    scraper = WebScraper(config)

    test_urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "http://web.simmons.edu/~grovesd/comm244/notes/week3/html-test-page.html",
    ]

    for i, url in enumerate(test_urls):
        print(f"🌐 Test {i + 1}/{len(test_urls)}: Analyzing {url}")
        print("-" * 60)

        document: Optional[ParsedDocument] = None
        try:
            start_time = time.time()
            document = scraper.fetch_page(url)
            end_time = time.time()
            fetch_duration = end_time - start_time

            print(f"✅ Successfully fetched in {fetch_duration:.2f}s")
            print(f"   Status: {document.response_info['status_code']}")
            print(f"   Final URL: {document.response_info['final_url']}")
            print(f"   Content Length: {document.response_info.get('content_length', 'N/A')} bytes")
            print(f"   Elements extracted: {len(document.elements)}")

            # Show document statistics
            print("\n📊 Document Statistics:")
            stats = document.get_document_stats()
            print(f"   Total elements: {stats['total_elements']}")
            print(f"   Unique tags: {stats['unique_tags']}")
            print(f"   Max depth: {stats['max_depth']}")
            print(f"   Avg depth: {stats['avg_depth']:.1f}")
            print(f"   Elements with classes: {stats['elements_with_classes']}")
            print(f"   Elements with IDs: {stats['elements_with_ids']}")
            print(f"   Elements with text: {stats['elements_with_text']}")

            print("\n🏷️  Most Common Tags:")
            for tag, count in stats['most_common_tags'].items():
                print(f"   {tag}: {count}")

            print("\n🎨 Element Types:")
            for elem_type, count in stats['element_types'].items():
                print(f"   {elem_type.capitalize()}: {count}") # Capitalize for display

            print("\n🔍 Sample Elements (first 8):")
            for j, el_info in enumerate(document.elements[:8]):
                text_preview = el_info.text[:50].replace('\n', ' ') + '...' if len(el_info.text) > 50 else el_info.text
                print(f"   {j+1}. <{el_info.tag}> classes=[{','.join(el_info.classes) or 'no-classes'}] depth={el_info.depth} children={el_info.children_count}")
                print(f"     Text: '{text_preview}'")
                print(f"     Signature: {document.generate_signature(el_info)}") # Use ParsedDocument's method
                print(f"     XPath: {el_info.xpath}")
                print()

            # --- NEW: Use detect_patterns and display PatternInfo ---
            print("🔁 Detecting Repeating Patterns (Sprint 2 Preview):")
            # Use the new detect_patterns method
            # For simplicity, we'll configure signature generation to only consider tag and classes_hash for now
            # This makes patterns more general, less sensitive to parent context/depth ranges initially.
            # You can adjust 'include_parent' and 'depth_levels' for generate_signature as needed.
            pattern_signature_config = {
                'include_parent': False, # For a broader initial pattern detection
                'depth_levels': 0        # Focuses on tag and classes_hash only
            }
            patterns = document.detect_patterns(min_threshold=2, pattern_signature_config=pattern_signature_config)

            if patterns:
                print(f"   Potential Repeating Patterns Found: {len(patterns)}")
                for sig, pattern_info in patterns.items():
                    sample_element = pattern_info.elements[0] # Get first element as a sample
                    text_preview = sample_element.text[:50].replace('\n', ' ') + '...' if len(sample_element.text) > 50 else sample_element.text
                    print(f"   Pattern: {sig} -> {pattern_info.count} occurrences")
                    print(f"     Sample: <{sample_element.tag}> '{text_preview}'")
            else:
                print("   No obvious repeating patterns detected (threshold=2)")
            # --- END NEW ---

        except Exception as e:
            print(f"❌ An unexpected error occurred for {url}: {e}")

        print("\n" + "=" * 60 + "\n")

    print("✨ Sprint 1 Demo Complete!")
    print("\nFeatures Successfully Demonstrated:")
    print("✅ HTTP fetching with error handling and timeouts")
    print("✅ HTML parsing and element extraction")
    print("✅ Element classification and property extraction")
    print("✅ Signature generation for element grouping")
    print("✅ Document statistics and analysis")
    print("✅ XPath generation for element location")
    print("✅ Memory-efficient processing")
    print("✅ **Enhanced Pattern Detection (Preview from Sprint 2)**")

    print("\n🚀 Ready for Sprint 2: Pattern Detection & Analysis!")

if __name__ == "__main__":
    demo_scraper()