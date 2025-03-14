import fitz
import regex as re
import os
import sys
import zipfile
import tempfile
from num2words import num2words

def ensure_lines_end_with_period(text):
    """
    Ensures each line ends with a period by merging lines until a period is reached.
    """
    lines = text.splitlines()
    new_lines = []
    buffer = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        buffer = buffer + " " + line if buffer else line
        if buffer.endswith('.'):
            new_lines.append(buffer)
            buffer = ""
    if buffer:  # Append any remaining text
        new_lines.append(buffer)
    return '\n'.join(new_lines)
def fix_name_abbreviations(text):
    """
    Fix abbreviations in names like "E. Zermelo" or "H.A. Simon" by removing periods
    after single capital letters that are likely initials.
    """
    # Pattern for single capital letter followed by period (and optional space) then another capital letter
    # This handles both "E. Z" and "E.Z" patterns
    pattern = r'(?<!\w)([A-Z])\.(\s*)(?=[A-Z])'
    
    # Replace with the capital letter and ensure there's a space
    return re.sub(pattern, r'\1 ', text)
def expand_abbreviations(text):
    """
    Expand common abbreviations in text
    """
    # Dictionary of common abbreviations and their expansions
    abbreviations = {
        r'\bMr\.': 'Mister',
        r'\bMrs\.': 'Misses',
        r'\bMs\.': 'Miss',
        r'\bDr\.': 'Doctor',
        r'\bProf\.': 'Professor',
        r'\bJr\.': 'Junior',
        r'\bSr\.': 'Senior',
        r'\bvs\.': 'versus',
        r'\betc\.': 'etcetera',
        r'\bi\.e\.': 'that is',
        r'\be\.g\.': 'for example',
        r'\bcf\.': 'compare',
        r'\bPh\.D\.': 'Doctor of Philosophy',
        r'\bM\.D\.': 'Medical Doctor',
        r'\bB\.A\.': 'Bachelor of Arts',
        r'\bM\.A\.': 'Master of Arts',
        r'\bU\.S\.': 'United States',
        r'\bU\.K\.': 'United Kingdom',
        r'\ba\.m\.': 'ante meridiem',
        r'\bp\.m\.': 'post meridiem',
        r'\bSt\.': 'Street',
        r'\bAve\.': 'Avenue',
        r'\bRd\.': 'Road',
        r'\bBlvd\.': 'Boulevard',
        r'\bDept\.': 'Department',
        r'\bUniv\.': 'University',
        r'\bCorp\.': 'Corporation',
        r'\bInc\.': 'Incorporated',
        r'\bLtd\.': 'Limited',
        r'\bCo\.': 'Company',
    }
    
    # Replace abbreviations
    for abbr, expansion in abbreviations.items():
        text = re.sub(abbr, expansion, text)
    
    # Fix name abbreviations (like "E. Zermelo")
    pattern = r'(?<!\w)([A-Z])\.(\s*)(?=[A-Z])'
    text = re.sub(pattern, r'\1 ', text)
    
    return text

def convert_numbers_to_words(text):
    """
    Convert numeric values to their word equivalents, handling 
    thousand separators and various number formats. Special handling for years.
    """
    from num2words import num2words
    
    # First replace commas between digits (thousand separators)
    text = re.sub(r'(\d),(\d)', r'\1\2', text)
    
    def replace_number(match):
        num_str = match.group(0)
        try:
            # Check if it's a decimal number
            if '.' in num_str:
                num = float(num_str)
                return num2words(num)
            else:
                num = int(num_str)
                
                # Special handling for years (between 1500 and 2100)
                if 1500 <= num <= 2100:
                    # Split year into first two digits and last two digits
                    first_part = num // 100
                    second_part = num % 100
                    
                    first_word = num2words(first_part)
                    
                    # Handle special cases for second part
                    if second_part == 0:
                        if num == 2000:
                            return "two thousand"
                        else:
                            return first_word + " hundred"
                    elif second_part < 10:
                        second_word = "oh-" + num2words(second_part)
                    else:
                        second_word = num2words(second_part)
                        
                    return first_word + " " + second_word
                else:
                    # Regular number conversion
                    return num2words(num)
                    
        except (ValueError, TypeError):
            # If conversion fails, return the original string
            return match.group(0)
    
    # Now convert all numbers to words
    number_pattern = r'\b\d+(\.\d+)?\b'
    text = re.sub(number_pattern, replace_number, text)
    
    return text
def handle_section_numbers(text):
    """
    Identify and specially format section numbers like 1.2. or 1.2.1. at the beginning of lines
    """
    # Pattern for lines starting with section numbers (1., 1.2., 1.2.3., etc.)
    section_pattern = r'(^|\n)(\d+(\.\d+)*)\.\s+'
    
    def section_replacement(match):
        section_num = match.group(2)  # The actual number pattern without the trailing dot
        parts = section_num.split('.')
        
        # Format based on depth
        if len(parts) == 1:
            prefix = "Section "
        elif len(parts) == 2:
            prefix = "Subsection "
        else:
            prefix = "Sub-subsection "
            
        # Create the formatted section reference
        formatted = prefix + " ".join(parts)
        
        # Preserve the newline if it exists, and add a space after the formatted section
        return (match.group(1) or '') + formatted + "."
    
    # Replace the section numbers
    return re.sub(section_pattern, section_replacement, text)

def clean_text(text):
    text = re.sub(r'\[\d+\]', '', text)
    # Merge hyphenated line breaks
    text = re.sub(r'-\n\s*', '', text)
    # Handle section numbers first
    text = handle_section_numbers(text)
    # Normalize spaces around punctuation
    text = re.sub(r'\s*([.,;!?])\s*', r'\1 ', text)
    
    # Expand abbreviations (do this before number conversion)
    text = expand_abbreviations(text)
    
    # Convert numbers to words
    text = convert_numbers_to_words(text)
    
    # Handle quoted content by placing it on its own line
    text = re.sub(r'"([^"]*)"', r'\n"\1"\n', text)  # Curly quotes
    text = re.sub(r'"([^"]*)"', r'\n"\1"\n', text)  # Straight quotes
    # Split text into lines for processing
    lines = text.splitlines()
    processed_lines = []
    buffer = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if buffer:
            buffer += " " + line
        else:
            buffer = line
        # Split at sentence-ending punctuation, respecting quotes
        if re.search(r'[.!?]$', buffer) and not re.search(r'["""]$', buffer):
            split_buffer = re.split(r'(?<=[.!?])\s+(?![""])', buffer)
            processed_lines.extend(split_buffer)
            buffer = ""
    if buffer:
        processed_lines.append(buffer)
    # Collapse excessive blank lines and spaces
    processed_lines = [line for line in processed_lines if line.strip()]
    processed_text = "\n".join(processed_lines)
    processed_text = re.sub(r'[ \t]{2,}', ' ', processed_text)
    # Add newlines after punctuation for TTS readability
    processed_text = re.sub(r'(?<=[.!?])\s*(?!\n)', '\n', processed_text)
    # Remove excessive blank lines
    processed_text = re.sub(r'\n{3,}', '\n\n', processed_text)
    # Additional replacements (some now handled by expand_abbreviations)
    # Remove trademark symbols
    processed_text = re.sub(r'™', '', processed_text)
    # Ensure every line ends with a period
    processed_text = ensure_lines_end_with_period(processed_text)
    return processed_text.strip()

def fix_text(text):
    """
    Joins lines that were split due to wrap-around.
    """
    lines = text.splitlines()
    fixed_lines = []
    i = 0
    while i < len(lines):
        current_line = lines[i]
        while (i < len(lines) - 1 and 
               re.search(r'[\p{L}]$', current_line) and 
               re.match(r'^[a-z]', lines[i+1].lstrip())):
            current_line += lines[i+1].lstrip()
            i += 1
        fixed_lines.append(current_line)
        i += 1
    return "\n".join(fixed_lines)

def additional_cleaning(text):
    """
    Applies additional cleaning rules:
    - Replace curly apostrophes with straight apostrophes.
    - Replace guillemets with curly quotes and then normalize them to straight quotes.
    - Replace "(" and ")" with commas.
    - Replace ";" with "."
    - Replace long dash "—" with " ,"
    - Replace "!" with "."
    """
    text = text.replace(chr(8216), "'").replace(chr(8217), "'")
    text = text.replace('«', chr(8220)).replace('»', chr(8221))
    text = text.replace(chr(8220), '"').replace(chr(8221), '"')
    text = re.sub(r'"', '', text)
    text = re.sub(r'^\s*\.\s*$', '', text, flags=re.MULTILINE)
    text = text.replace('(', ',').replace(')', ',')
    text = text.replace(';', '.')
    text = text.replace('—', ' ,')
    text = text.replace('!', '.')
    return text

def extract_cleaned_text(doc, header_threshold=50, footer_threshold=50):
    all_pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("blocks")
        page_height = page.rect.height
        page_width = page.rect.width

        filtered_lines = []
        for block in blocks:
            x0, y0, x1, y1, text, btype = block[:6]
            # Exclude headers/footers
            if y1 < header_threshold:
                continue
            elif y0 > page_height - footer_threshold:
                continue
            # Exclude page numbers
            if re.match(r'^\d+$', text.strip()):
                continue
            # Exclude very small blocks
            block_width = x1 - x0
            block_height = y1 - y0
            if block_width < 0.1 * page_width and block_height < 0.1 * page_height:
                continue
            # Process each line in the block to remove trailing hyphens or hyphen-space
            lines = text.splitlines()
            cleaned_lines = []
            for line in lines:
                # Remove trailing whitespace first
                line = line.rstrip()
                # Check for trailing "- " or "-"
                if line.endswith('- '):
                    line = line[:-2]  # Remove "- " (hyphen and space)
                    
                elif line.endswith('-'):
                    line = line[:-1]  # Remove just "-"
                cleaned_lines.append(line)
            # Rejoin the lines into block text
            block_text = "\n".join(cleaned_lines)
            filtered_lines.append(block_text)

        page_text = "\n".join(filtered_lines)
        all_pages.append(page_text)
    return all_pages

def get_table_of_contents(doc):
    toc = doc.get_toc()
    if not toc:
        print("No TOC found in the document.")
        return []
    else:
        print(f"Table of Contents extracted with {len(toc)} entries.")
    return toc

def deduplicate_toc(toc):
    seen_pages = set()
    deduplicated_toc = []
    for entry in toc:
        level, title, page_number = entry
        if page_number not in seen_pages:
            deduplicated_toc.append(entry)
            seen_pages.add(page_number)
        else:
            print(f"Duplicate TOC entry removed: {entry}")
    return deduplicated_toc

def remove_overlap(prev_text, curr_text):
    prev_lines = prev_text.splitlines()
    curr_lines = curr_text.splitlines()
    for overlap_size in range(min(len(prev_lines), len(curr_lines)), 0, -1):
        if prev_lines[-overlap_size:] == curr_lines[:overlap_size]:
            return "\n".join(prev_lines[:-overlap_size])
    return prev_text

def structure_text_by_toc(toc, all_pages_text):
    chapters = []
    last_chapter_text = None
    last_title = None
    last_level = None
    for i, entry in enumerate(toc):
        level, title, start_page = entry
        start_page_idx = start_page - 1
        if i < len(toc) - 1:
            _, _, next_page = toc[i + 1]
            end_page_idx = max(start_page_idx, next_page - 1)
        else:
            end_page_idx = len(all_pages_text) - 1
        chapter_pages = all_pages_text[start_page_idx:end_page_idx]
        chapter_text = "".join(chapter_pages)
        # Apply cleaning
        chapter_text = clean_text(chapter_text)
        chapter_text = additional_cleaning(chapter_text)
        clean_title = title.strip('\r\n')
        if last_chapter_text is not None:
            last_chapter_text = remove_overlap(last_chapter_text, chapter_text)
            chapters.append((last_level, last_title, last_chapter_text))
        last_chapter_text = chapter_text
        last_title = clean_title
        last_level = level
    if last_chapter_text is not None:
        chapters.append((last_level, last_title, last_chapter_text))
    return chapters

def save_whole_book(book_name, all_pages_text, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = os.path.join(output_dir, f"{book_name}_full_text.txt")
    full_text = "\n".join(all_pages_text)
    full_text = clean_text(full_text)
    full_text = additional_cleaning(full_text)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"All content saved to: {output_file}")
def save_chapters(chapters, book_name, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    padding = len(str(len(chapters)))
    for idx, (level, title, text) in enumerate(chapters, 1):
        safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', title)
        safe_title = safe_title.strip().replace(' ', '_')
        if not safe_title:
            safe_title = f"chapter_{idx}"
        filename = f"{str(idx).zfill(padding)}_{safe_title}.txt"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
    print(f"Chapters saved in directory: {output_dir}")

def parse_epub(epub_path, output_dir, progress_callback=None):
    """
    Parse an EPUB file and extract chapters based on the internal file structure.
    
    Args:
        epub_path: Path to the EPUB file
        output_dir: Directory to save extracted content
        progress_callback: Optional callback function for progress updates
    """
    if progress_callback:
        progress_callback(10)
        
    try:
        # Open the document with PyMuPDF for metadata
        doc = fitz.open(epub_path)
        print(f"Successfully opened '{os.path.basename(epub_path)}'")
        
        # Get metadata
        metadata = doc.metadata
        book_title = metadata.get("title") if metadata.get("title") else os.path.splitext(os.path.basename(epub_path))[0]
        
        # Clean the book title to use as a folder name
        safe_title = re.sub(r'[^\w\s-]', '', book_title).strip().replace(' ', '_')
        if not safe_title:
            safe_title = "unnamed_book"
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        if progress_callback:
            progress_callback(30)
            
        # Extract content directly from the EPUB zip structure
        with zipfile.ZipFile(epub_path, 'r') as epub_zip:
            # Find the content files (HTML files)
            content_files = [f for f in epub_zip.namelist() if f.endswith(('.html', '.xhtml', '.htm'))]
            
            # Sort the files - many EPUBs have numbered filenames
            content_files.sort()
            
            print(f"Found {len(content_files)} content files inside EPUB")
            
            if progress_callback:
                progress_callback(50)
                
            # Create a temporary directory to extract individual files
            with tempfile.TemporaryDirectory() as temp_dir:
                total_files = len(content_files)
                
                # Extract each content file as a separate chapter
                for i, html_file in enumerate(content_files):
                    try:
                        # Extract the file to temp directory
                        extracted_path = os.path.join(temp_dir, os.path.basename(html_file))
                        with open(extracted_path, 'wb') as f:
                            f.write(epub_zip.read(html_file))
                        
                        # Use PyMuPDF to extract the formatted text
                        try:
                            html_doc = fitz.open(extracted_path)
                            if html_doc.page_count > 0:
                                text = ""
                                for page_num in range(html_doc.page_count):
                                    page = html_doc.load_page(page_num)
                                    text += page.get_text("text") + "\n\n"
                                
                                # Perform text cleanup
                                text = clean_text(text)
                                text = additional_cleaning(text)
                                
                                # Name files with padding for proper sorting
                                padding = len(str(total_files))
                                output_file = os.path.join(output_dir, f"{str(i).zfill(padding)}_Chapter_{i}.txt")
                                
                                with open(output_file, "w", encoding="utf-8") as f:
                                    f.write(text)
                                
                                print(f"Extracted: Chapter {i} (from {html_file})")
                            
                            html_doc.close()
                            
                            # Update progress
                            if progress_callback:
                                progress = 50 + int((i / total_files) * 50)
                                progress_callback(progress)
                                
                        except Exception as e:
                            print(f"Error processing {html_file} with PyMuPDF: {e}")
                            
                    except Exception as e:
                        print(f"Error extracting {html_file}: {e}")
        
        print(f"Extracted content saved to {output_dir}")
        if progress_callback:
            progress_callback(100)
            
        doc.close()
        return output_dir
        
    except Exception as e:
        print(f"Error processing {epub_path}: {e}")
        if 'doc' in locals():
            doc.close()
        raise e
    
def extract_book(file_path, use_toc=True, extract_mode="chapters", output_dir="extracted_books", progress_callback=None):
    if progress_callback:
        progress_callback(10)
        
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File '{file_path}' does not exist.")
        
    # Determine file type by extension
    file_ext = os.path.splitext(file_path)[1].lower()
    book_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    if file_ext == '.epub':
        # Process EPUB file
        return parse_epub(file_path, output_dir, progress_callback)
    elif file_ext == '.pdf':
        # Process PDF file (existing functionality)
        doc = fitz.open(file_path)
        all_pages_text = extract_cleaned_text(doc)
        toc = get_table_of_contents(doc)
        deduplicated_toc = deduplicate_toc(toc)
        
        if use_toc and deduplicated_toc and extract_mode == "chapters":
            chapters = structure_text_by_toc(deduplicated_toc, all_pages_text)
            save_chapters(chapters, book_name, output_dir)
        else:
            save_whole_book(book_name, all_pages_text, output_dir)
        
        doc.close()
        print("Extraction complete.")
        if progress_callback:
            progress_callback(100)
        return output_dir
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: .pdf, .epub")
'''
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract.py <pdf_path>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    try:
        extract_book(pdf_path, use_toc=True, extract_mode="chapters", output_dir="extracted_books")
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)
'''