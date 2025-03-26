import fitz # PyMuPDF
import regex as re
import os
import sys
import zipfile
import tempfile
import time
import unicodedata # For normalization
from bs4 import BeautifulSoup # For improved EPUB parsing
from num2words import num2words

# --- Configuration ---
# Could be externalized later
HEADER_THRESHOLD = 50 # Pixels from top to ignore
FOOTER_THRESHOLD = 50 # Pixels from bottom to ignore
MIN_BLOCK_WIDTH_RATIO = 0.1 # Minimum block width relative to page width
MIN_BLOCK_HEIGHT_RATIO = 0.1 # Minimum block height relative to page height

# --- Text Cleaning and Processing Functions ---

def normalize_text(text):
    """Apply Unicode normalization and fix common problematic characters."""
    # NFKC decomposes ligatures and compatibility characters
    text = unicodedata.normalize('NFKC', text)
    # Specific replacements for characters normalization might not handle as desired
    text = text.replace('—', ', ') # Em dash with comma space (often better for TTS pause)
    text = text.replace('–', ', ') # En dash
    text = text.replace('«', '"').replace('»', '"') # Guillemets to standard quotes
    # Replace various apostrophe/quote types with standard ones
    text = text.replace(chr(8216), "'").replace(chr(8217), "'") # ‘ ’ -> '
    text = text.replace(chr(8220), '"').replace(chr(8221), '"') # “ ” -> "
    # Add spaces around hyphens used as separators (like in ranges, if desired)
    # text = re.sub(r'(?<=\w)-(?=\w)', ' - ', text) # Optional: might affect compound words

    # Fix specific odd characters observed (add more if found)
    # text = text.replace('ĕ', 'e') # If 'ĕ' consistently represents 'e' due to font issues
    # text = text.replace('', 'Th') # If Th ligature consistently causes issues

    return text

def expand_abbreviations_and_initials(text):
    """Expand common abbreviations and fix spaced initials."""
    abbreviations = {
        r'\bMr\.': 'Mister', r'\bMrs\.': 'Misses', r'\bMs\.': 'Miss', r'\bDr\.': 'Doctor',
        r'\bProf\.': 'Professor', r'\bJr\.': 'Junior', r'\bSr\.': 'Senior',
        r'\bvs\.': 'versus', r'\betc\.': 'etcetera', r'\bi\.e\.': 'that is',
        r'\be\.g\.': 'for example', r'\bcf\.': 'compare', r'\bSt\.': 'Saint', # Changed St. -> Saint, more common? Or 'Street'? Needs context. Assume Saint for now.
        r'\bVol\.': 'Volume', r'\bNo\.': 'Number', r'\bpp\.': 'pages', r'\bp\.': 'page',
        # Add more domain-specific ones if needed
    }
    # Expand standard abbreviations
    for abbr, expansion in abbreviations.items():
        text = re.sub(abbr, expansion, text, flags=re.IGNORECASE)

    # Fix initials like "E. B. White" -> "E B White"
    # Looks for sequences of (CapitalLetter + Period + OptionalSpace) followed by another CapitalLetter
    # Using positive lookahead to handle sequences correctly.
    text = re.sub(r'([A-Z])\.(?=\s*[A-Z])', r'\1', text)
    # Clean up any potential double spaces left by the above
    text = re.sub(r' +', ' ', text)

    return text

def convert_numbers(text):
    """Convert integers and years to words. Leaves decimals and other numbers."""
    # Replace commas in numbers (thousand separators)
    text = re.sub(r'(?<=\d),(?=\d)', '', text)

    def replace_match(match):
        num_str = match.group(0)
        try:
            # Handle potential decimals - leave them as digits for now, TTS often handles them well
            if '.' in num_str:
                return num_str
            num = int(num_str)
            # Year handling (common range)
            if 1500 <= num <= 2100:
                return num2words(num, to='year')
            # Handle ordinal numbers (e.g., 1st, 2nd)
            elif match.group(1):
                 # Convert the number part and append the suffix
                 return num2words(num, to='ordinal') + match.group(1)
            # Default: convert cardinal numbers
            else:
                 # Optional: Add threshold? Only convert small numbers?
                 # if num < 1000: return num2words(num) else: return num_str
                 return num2words(num)
        except ValueError:
            return num_str # Return original if not a valid number

    # Regex to find integers possibly followed by ordinal suffixes (st, nd, rd, th)
    # We target whole numbers primarily, potentially with ordinal indicators
    pattern = r'\b(\d+)(st|nd|rd|th)?\b'
    text = re.sub(pattern, replace_match, text)
    return text

def handle_sentence_ends_and_pauses(text):
    """Ensure sentences end cleanly and handle potential pauses."""
    # Add a space before punctuation if missing (helps TTS parsing)
    text = re.sub(r'(?<=\w)([.,!?;:])', r' \1', text)
    # Normalize multiple spaces
    text = re.sub(r' +', ' ', text)

    # Ensure common sentence endings have a period if missing (e.g. lists)
    # This is less aggressive than forcing periods everywhere
    lines = text.splitlines()
    processed_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line and not re.search(r'[.!?;:]$', stripped_line):
             # Check if it looks like a list item or short phrase unlikely to be a full sentence
             if not re.match(r'^[-\*\u2022\d+\.\s]+', stripped_line) and len(stripped_line.split()) > 3:
                 line += '.' # Add period only if it seems like a sentence fragment
        processed_lines.append(line)
    text = '\n'.join(processed_lines)

    # Replace semicolons with commas (often better for TTS pause)
    text = text.replace(';', ',')
    # Replace hyphens used as pauses (like in dialogues) with commas
    text = re.sub(r' - ', ', ', text)
    # Optional: Replace exclamation marks with periods if excitement is not desired
    # text = text.replace('!', '.')
    # Optional: Replace question marks with periods if intonation is not desired
    # text = text.replace('?', '.')

    # Add newline after sentence-ending punctuation for potential TTS break cues
    # Ensure space exists after punctuation before newline
    text = re.sub(r'([.!?:]) +', r'\1\n', text)

    return text

def remove_artifacts(text):
    """Remove common extraction artifacts like citations, excessive newlines etc."""
    # Remove bracketed numbers (citations, footnotes)
    text = re.sub(r'\[\d+\]', '', text)
    # Remove page numbers (simple standalone numbers on a line) - might need refinement
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    # Remove lines that are just punctuation (often artifacts)
    text = re.sub(r'^\s*[.,;:!?\-]+\s*$', '', text, flags=re.MULTILINE)
    # Collapse multiple blank lines into a single blank line
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Remove leading/trailing whitespace from the whole text
    text = text.strip()
    return text

def join_wrapped_lines(text):
    """Join lines that seem to be wrapped mid-sentence."""
    lines = text.splitlines()
    result_lines = []
    if not lines:
        return ""

    buffer = lines[0]
    for i in range(1, len(lines)):
        current_line = lines[i]
        prev_line = lines[i-1] # Check previous line for ending punctuation

        # Heuristic: Join if previous line doesn't end with sentence punctuation
        # AND current line starts with lowercase (or is continuation of list/quote)
        # This tries to avoid joining across paragraphs.
        if (not re.search(r'[.!?:"]$', prev_line.strip()) and
            re.match(r'^[a-z]', current_line.strip())): # Basic check for lowercase start
             buffer += " " + current_line.strip()
        else:
             # If previous line looks like end of sentence, or current line looks like start of new paragraph
             result_lines.append(buffer.strip())
             buffer = current_line # Start new buffer

    result_lines.append(buffer.strip()) # Add the last buffer content
    return '\n'.join(filter(None, result_lines)) # Join non-empty lines

def basic_html_to_text(html_content):
    """Extract text from HTML using BeautifulSoup, removing scripts/styles."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    # Get text, joining paragraphs/blocks with double newlines
    # Use strip=True to remove extra whitespace around tags
    # Use separator='\n' to ensure block elements get newlines between them
    text = soup.get_text(separator='\n', strip=True)

    # Collapse multiple spaces resulting from inline tags
    text = re.sub(r'[ \t]+', ' ', text)
    # Collapse multiple newlines into max two (paragraph break)
    text = re.sub(r'\n\s*\n', '\n\n', text)

    return text

def clean_pipeline(text):
    """Apply the full cleaning pipeline in order."""
    if not text: return ""
    text = normalize_text(text)
    # print("--- After normalize ---\n", text[:500]) # Debug
    text = join_wrapped_lines(text) # Join lines first
    # print("--- After join lines ---\n", text[:500]) # Debug
    text = expand_abbreviations_and_initials(text)
    # print("--- After abbreviations ---\n", text[:500]) # Debug
    text = convert_numbers(text)
    # print("--- After numbers ---\n", text[:500]) # Debug
    text = handle_sentence_ends_and_pauses(text)
    # print("--- After sentence ends ---\n", text[:500]) # Debug
    text = remove_artifacts(text)
    # print("--- After artifacts ---\n", text[:500]) # Debug
    # Final whitespace cleanup
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n+', '\n', text).strip() # Ensure single newlines mostly
    return text


# --- PDF Extraction ---

def extract_pdf_text(doc):
    """Extract text from PDF pages, filtering headers/footers."""
    all_pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_height = page.rect.height
        page_width = page.rect.width

        # Extract text blocks
        blocks = page.get_text("blocks", flags=fitz.TEXTFLAGS_TEXT) # Basic flags
        filtered_lines = []
        for block in blocks:
            x0, y0, x1, y1, text, *_ = block # block_no, block_type might be present
            # Filter by position (header/footer)
            if y1 < HEADER_THRESHOLD or y0 > page_height - FOOTER_THRESHOLD:
                continue
            # Filter small blocks (potential noise) - adjust ratios if needed
            # block_width = x1 - x0
            # block_height = y1 - y0
            # if block_width < MIN_BLOCK_WIDTH_RATIO * page_width and block_height < MIN_BLOCK_HEIGHT_RATIO * page_height:
            #     continue

            # Simple text cleaning per block (remove excess whitespace)
            cleaned_block_text = re.sub(r'\s+', ' ', text).strip()
            if cleaned_block_text:
                filtered_lines.append(cleaned_block_text)

        page_text = "\n".join(filtered_lines) # Join blocks with newline for structure
        all_pages.append(page_text)
    return "\n".join(all_pages) # Join pages


def get_toc(doc):
    """Extract and print TOC from PDF."""
    toc = doc.get_toc()
    if not toc:
        print("  No Table of Contents found in the document.")
        return []
    else:
        print(f"  Table of Contents extracted with {len(toc)} entries.")
        return toc

def structure_by_toc(toc, full_text):
    """Structure the full text into chapters based on TOC page numbers."""
    # This simplistic approach assumes page numbers directly map to text boundaries.
    # A more robust method might involve searching for titles near page breaks.
    # For now, we'll just use it to get titles and split the *already extracted* text.
    # NOTE: This function assumes `full_text` is the entire book as one string.
    # It doesn't use page numbers for splitting, only for chapter titles/order.
    # A better approach would use the page numbers during extraction or map them.
    # Given the limitations, let's just return titles for now.
    chapters = []
    print("  Structuring by TOC (using titles only for now)...")
    for level, title, page_num in toc:
         # Clean title
         clean_title = title.strip()
         chapters.append({'level': level, 'title': clean_title, 'page': page_num})
    return chapters # Returns list of dicts with title info


# --- EPUB Extraction ---

def parse_epub_content(epub_path, progress_callback=None):
    """
    Extracts and cleans text content from EPUB using BeautifulSoup.

    Returns:
        list[dict]: A list of chapters, each with 'title' (filename) and 'text'.
    """
    chapters = []
    print(f"  Processing EPUB: '{os.path.basename(epub_path)}'")
    extracted_files_count = 0

    try:
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            # Find the OPF file (usually content.opf)
            opf_path = None
            for item in epub_zip.namelist():
                if item.lower().endswith('.opf'):
                    opf_path = item
                    break
            if not opf_path:
                print("  Error: Could not find OPF file in EPUB.")
                # Fallback: process all HTML/XHTML files naively
                content_files = sorted([f for f in epub_zip.namelist() if f.lower().endswith(('.html', '.xhtml', '.htm'))])
                manifest_items = [{'href': f} for f in content_files] # Create dummy manifest
                spine_order = content_files # Assume alphabetical order
            else:
                print(f"  Found OPF file: '{opf_path}'")
                # Parse OPF to get manifest and spine
                opf_content = epub_zip.read(opf_path).decode('utf-8')
                opf_soup = BeautifulSoup(opf_content, 'xml') # Use 'xml' parser for OPF
                manifest_items = {}
                for item in opf_soup.find('manifest').find_all('item'):
                    manifest_items[item.get('id')] = {'href': item.get('href'), 'media-type': item.get('media-type')}

                spine_order = [item.get('idref') for item in opf_soup.find('spine').find_all('itemref')]
                print(f"  Found {len(manifest_items)} manifest items and {len(spine_order)} spine items.")

            # Process files in spine order
            total_files_in_spine = len(spine_order)
            epub_base_path = os.path.dirname(opf_path) if opf_path else '' # Base path for relative links

            for i, idref in enumerate(spine_order):
                item = manifest_items.get(idref)
                if not item or 'html' not in item.get('media-type', ''):
                    print(f"    Skipping non-HTML spine item: {idref}")
                    continue

                # Construct full path within zip relative to OPF directory
                relative_href = item.get('href')
                # Handle potential path differences - join relative to OPF dir
                content_path = os.path.normpath(os.path.join(epub_base_path, relative_href)).replace('\\', '/') # Normalize path separators for zip

                if progress_callback:
                    progress_callback(10 + int((i / total_files_in_spine) * 80))

                try:
                    html_content = epub_zip.read(content_path).decode('utf-8', errors='ignore')
                    print(f"    [{i+1}/{total_files_in_spine}] Reading: '{content_path}'")
                    # Extract text using BeautifulSoup
                    raw_text = basic_html_to_text(html_content)
                    # Apply full cleaning pipeline
                    cleaned_text = clean_pipeline(raw_text)

                    if cleaned_text: # Only add chapter if it has content
                         chapters.append({
                             'title': os.path.basename(relative_href), # Use filename as temp title
                             'text': cleaned_text
                         })
                         extracted_files_count += 1
                    else:
                         print(f"      No text content extracted from '{content_path}'.")

                except KeyError:
                    print(f"    Error: File path not found in zip for idref '{idref}': '{content_path}'")
                except Exception as e:
                    print(f"    Error processing content file '{content_path}': {e}")
                    # traceback.print_exc() # Uncomment for detailed debug

            print(f"  Successfully extracted text from {extracted_files_count} content files.")
            if progress_callback: progress_callback(95) # Near end before saving

    except Exception as e:
        print(f"  Error opening or processing EPUB file '{epub_path}': {e}")
        raise # Re-raise error

    return chapters

# --- Saving Functions ---

def save_chapters_generic(chapters, book_name, output_dir):
    """Saves chapters (list of dicts with 'title', 'text') to files."""
    if not chapters:
        print("  No chapters found or extracted to save.")
        return
    os.makedirs(output_dir, exist_ok=True)
    num_chapters = len(chapters)
    padding = len(str(num_chapters))
    print(f"  Saving {num_chapters} chapters to '{output_dir}'...")

    for idx, chapter in enumerate(chapters, 1):
        title = chapter.get('title', f'Chapter_{idx}')
        text = chapter.get('text', '')

        # Create a safer filename from the title
        safe_title = re.sub(r'[^\w\s-]', '', title).strip() # Allow word chars, whitespace, hyphen
        safe_title = re.sub(r'\s+', '_', safe_title) # Replace whitespace with underscore
        if not safe_title: safe_title = f"chapter_{idx}"
        # Truncate long filenames if necessary
        max_len = 50 # Limit filename length
        safe_title = safe_title[:max_len]

        filename = f"{str(idx).zfill(padding)}_{safe_title}.txt"
        filepath = os.path.join(output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            print(f"    Error saving chapter '{filename}': {e}")

    print(f"  Finished saving chapters.")


def save_whole_book_text(full_text, book_name, output_dir):
    """Cleans and saves the entire book text to a single file."""
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{book_name}_full_text.txt")
    print(f"  Cleaning full text...")
    cleaned_full_text = clean_pipeline(full_text) # Apply cleaning pipeline
    print(f"  Saving full text to '{output_file}'...")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_full_text)
        print(f"  Full text saved.")
    except Exception as e:
        print(f"  Error saving full text: {e}")

# --- Main Extraction Function ---

def extract_book(file_path, use_toc=True, extract_mode="chapters", output_dir="extracted_books", progress_callback=None):
    """
    Extracts text from PDF or EPUB files, cleans it, and saves chapters or whole text
    directly into the specified output_dir.

    Args:
        file_path (str): Path to the PDF or EPUB file.
        use_toc (bool): If True, attempts to use TOC for structuring (PDF only currently).
        extract_mode (str): 'chapters' or 'whole'.
        output_dir (str): The EXACT directory where text files should be saved.
        progress_callback (callable, optional): Reports progress (0-100).

    Returns:
        str: The path to the directory where text was saved (same as output_dir).

    Raises:
        FileNotFoundError: If file_path does not exist.
        ValueError: If file format is unsupported.
        Exception: For other processing errors.
    """
    start_time = time.time()
    if progress_callback: progress_callback(0)

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Input file not found: '{file_path}'")

    file_ext = os.path.splitext(file_path)[1].lower()
    book_name_base = os.path.splitext(os.path.basename(file_path))[0]
    # We still need the book name for potential single file saving, but NOT for directory creation
    safe_book_name = re.sub(r'[^\w\s-]', '', book_name_base).strip().replace(' ', '_')
    if not safe_book_name: safe_book_name = "unnamed_book"


    # --- Ensure the TARGET output directory exists ---
    # This directory (e.g., extracted_books/Book_Name_Original) is provided by the caller (UI)
    os.makedirs(output_dir, exist_ok=True)
    print(f"--- Starting Extraction for: {os.path.basename(file_path)} ---")
    print(f"    Output directory       : {output_dir}") # Log the actual target directory

    try:
        if file_ext == '.pdf':
            print("  Processing PDF file...")
            if progress_callback: progress_callback(10)
            doc = fitz.open(file_path)
            print(f"  Opened PDF. Pages: {len(doc)}")

            if progress_callback: progress_callback(20)
            full_text = extract_pdf_text(doc)
            print(f"  Extracted raw text (length: {len(full_text)}).")

            if progress_callback: progress_callback(60)

            if extract_mode == "chapters":
                 toc = get_toc(doc)
                 if use_toc and toc:
                     # TODO: Enhance structure_by_toc for PDF chapter splitting
                     print("  TOC found for PDF, but chapter splitting is basic. Saving as whole book.")
                     # Pass output_dir directly
                     save_whole_book_text(full_text, safe_book_name, output_dir)
                 else:
                     print("  No TOC used or found. Saving as whole book text.")
                     # Pass output_dir directly
                     save_whole_book_text(full_text, safe_book_name, output_dir)
            else: # extract_mode == "whole"
                print("  Saving as whole book text.")
                # Pass output_dir directly
                save_whole_book_text(full_text, safe_book_name, output_dir)

            doc.close()
            if progress_callback: progress_callback(95)

        elif file_ext == '.epub':
            print("  Processing EPUB file...")
            # Use the improved BeautifulSoup-based parser
            chapters = parse_epub_content(file_path, progress_callback) # Progress handled inside

            if extract_mode == "chapters":
                 # Pass output_dir directly
                 save_chapters_generic(chapters, safe_book_name, output_dir)
            else: # extract_mode == "whole"
                 print("  Combining EPUB chapters into whole book text...")
                 full_text = "\n\n".join([chap['text'] for chap in chapters])
                 # Pass output_dir directly
                 save_whole_book_text(full_text, safe_book_name, output_dir)

        else:
            raise ValueError(f"Unsupported file format: '{file_ext}'. Supported: .pdf, .epub")

        elapsed_time = time.time() - start_time
        print(f"--- Extraction completed in {elapsed_time:.2f} seconds ---")
        if progress_callback: progress_callback(100)
        # Return the directory where files were actually saved
        return output_dir

    except Exception as e:
        print(f"!!! Error during extraction for '{file_path}': {e}")
        # traceback.print_exc() # Uncomment for full traceback during debugging
        if progress_callback: progress_callback(None) # Indicate error
        raise # Re-raise the exception to be caught by the UI
# --- Example Usage (commented out) ---
'''
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract.py <file_path>")
        sys.exit(1)
    file_arg = sys.argv[1]
    output_base_dir = "extracted_test" # Example output base

    def sample_progress(p):
         if p is not None:
              print(f"Progress: {p:.0f}%")
         else:
              print("Progress: Error!")

    try:
        result_dir = extract_book(
            file_arg,
            use_toc=True,          # Try TOC for PDF
            extract_mode="chapters", # Extract chapters if possible
            output_dir=output_base_dir,
            progress_callback=sample_progress
        )
        print(f"\nExtraction successful. Output saved in: {result_dir}")
    except Exception as e:
        print(f"\nExtraction failed: {e}")
        sys.exit(1)
'''