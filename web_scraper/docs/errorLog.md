# Trials and Tribulations: Pytest Debugging Log

## sprint 1

This document serves as a log of errors encountered during the development and testing of the web scraping library, along with their root causes and solutions. It highlights common pitfalls in Python testing, especially when dealing with floating-point comparisons and string/hash matching.

---

## Issue 1: `test_document.py::test_get_document_stats` - `avg_depth` Assertion Failure

**Error Message:**

```
E assert 2.6363636363636362 == 2.64 ± 2.6e-06
E
E comparison failed
E Obtained: 2.6363636363636362
E Expected: 2.64 ± 2.6e-06
```

**Reason:**
The test was asserting that the `avg_depth` was `2.64` using `pytest.approx()`. While `pytest.approx()` handles floating-point comparisons with a tolerance, the actual calculated average depth for the `simple_html_doc` fixture was `29 / 11 = 2.6363636363636362`. The difference between `2.64` and `2.63636...` was slightly larger than the default or implicitly set tolerance of `pytest.approx()`, leading to a comparison failure.

**Solution:**
Adjusted the expected value in the assertion to the precise calculated floating-point number.

```python
# In tests/test_document.py
# Old: assert stats['avg_depth'] == pytest.approx(2.64)
assert stats['avg_depth'] == pytest.approx(29 / 11) # Or pytest.approx(2.6363636363636362)
```

#### Issue 2: test_document.py::test_get_document_stats - element_types Assertion Failure

Error Message:

```
E       AssertionError: assert 'Content' in {'content': 7, 'interactive': 1, 'metadata': 3}
```

Reason:
The element_types dictionary returned by get_document_stats() stored element type counts using lowercase keys (e.g., 'content'). The test, however, was asserting for an uppercase key ('Content'). Python dictionary keys are case-sensitive.

Solution:
Changed the assertion to use the correct lowercase key. Likewise for the following assertions.

```Python

# In tests/test_document.py
# Old: assert 'Content' in stats['element_types']
assert 'content' in stats['element_types']
```

#### Issue 3: test_document.py::test_find_potential_patterns - StopIteration (Incorrect Fixture Expectation)

Error Message:

```
E       StopIteration
test_document.py:90: StopIteration
```

This occurred on the line: p_sig = next(s for s, elems in patterns.items() if s.tag == 'p' and s.classes_hash == expected_p_classes_hash)

Reason:
The test_find_potential_patterns test uses the simple_html_doc fixture. The <p> tags in this fixture have class="text". However, the test was incorrectly calculating expected_p_classes_hash based on the string "item": hashlib.md5("item".encode()).hexdigest()[:8]. Since no <p class="item"> elements existed in simple_html_doc, the next() call could not find a matching ElementSignature, leading to StopIteration.

Solution:
Adjusted the hash calculation in the test to match the actual class name ("text") present in the simple_html_doc fixture. There were similar errors littered across the test file.Changed them all.

# In tests/test_document.py (within test_find_potential_patterns)

```
import hashlib # Ensure this is at the top of the file
```

```
# Old: expected_p_classes_hash = hashlib.md5("item".encode()).hexdigest()[:8]

# Old: p_sig = next(s for s, elems in patterns.items() if s.tag == 'p' and s.classes_hash == expected_p_classes_hash)
```

# Corrected for simple_html_doc: 'p' tags have class="text"

```
expected_p_classes_hash_for_text = hashlib.md5("text".encode()).hexdigest()[:8]
p_sig = next(s for s, elems in patterns.items() if s.tag == 'p' and s.classes_hash == expected_p_classes_hash_for_text)
```

##### Issue 4: test_document.py::test_find_potential_patterns_with_multiple_types - StopIteration (Incorrect classes_hash Comparison Logic)

Error Message:

```
E StopIteration
test_document.py:134: StopIteration
```

This occurred on the line: p_item_sig = next(s for s, elems in patterns.items() if s.tag == 'p' and "item" in s.classes_hash)

Reason:
The ElementSignature's classes_hash attribute stores an 8-character MD5 hash (e.g., 'b1e0f06f') of the sorted, joined class names, not the literal class names themselves. The test was incorrectly attempting to check if the string "item" was in the hash string ("item" in s.classes_hash). This condition would always evaluate to False, as the hash string would never contain the literal substring "item". Consequently, next() failed to find the expected signature.

Solution:
Calculated the expected classes_hash for the class "item" (which is relevant for the html_with_patterns_doc fixture) and then directly compared s.classes_hash with this calculated hash.
Python

# In tests/test_document.py (within test_find_potential_patterns_with_multiple_types)

```
import hashlib # Ensure this is at the top of the file
```

```
# Old: p_item_sig = next(s for s, elems in patterns.items() if s.tag == 'p' and "item" in s.classes_hash)

# Corrected: Compare classes_hash to the actual calculated hash of 'item'

expected_p_item_classes_hash = hashlib.md5("item".encode()).hexdigest()[:8]
p_item_sig = next(s for s, elems in patterns.items() if s.tag == 'p' and s.classes_hash == expected_p_item_classes_hash)
```

#### Issue 5: test_settings.py::test_web_scraping_config_defaults - user_agent Assertion Failure

Error Message:

```
E AssertionError: assert 'WebScraperLibrary/1.0' == 'WebScraperDemo/1.0'
E
E - WebScraperDemo/1.0
E + WebScraperLibrary/1.0
```

Reason:
The default user_agent string defined in the WebScrapingConfig class (likely in web_scraper/config/settings.py) was "WebScraperLibrary/1.0". However, the unit test in test_settings.py was asserting that the default user_agent should be "WebScraperDemo/1.0". This was a mismatch between the actual default value and the expected value in the test.

Solution:
Updated the user_agent assertions in test_settings.py to reflect the correct default value from WebScrapingConfig.
Python

# In tests/test_settings.py

```
 Old: assert config.user_agent == "WebScraperDemo/1.0"

assert config.user_agent == "WebScraperLibrary/1.0"

# Also updated the headers assertion for consistency

# Old: assert config.headers['User-Agent'] == "WebScraperDemo/1.0"

assert config.headers['User-Agent'] == "WebScraperLibrary/1.0"
```

Conclusion:

These debugging sessions highlighted the importance of:

- Precision in Floating-Point Comparisons: Using pytest.approx() is crucial, but understanding its tolerance and providing precise expected values (e.g., 29/11) is key.
- Exact String/Hash Matching: When dealing with generated hashes or complex string attributes, always verify the exact format and content. Avoid in checks where a direct == comparison to a precisely calculated expected value is necessary.
- Test-Code Alignment: Ensuring that unit tests accurately reflect the default or expected behavior of the actual code. Any change in defaults in the application code must be mirrored in the tests.
- Careful Fixture Inspection: Always double-check the content and structure of fixtures to ensure the test assertions align with the data provided by the fixture.
