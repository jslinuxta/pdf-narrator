import fitz
import regex as re
import os
import sys

def clean_text(text):
    import regex as re

    # Merge hyphenated line breaks
    text = re.sub(r'-\n\s*', '', text)

    # Normalize spaces around punctuation
    text = re.sub(r'\s*([.,;!?])\s*', r'\1 ', text)

    # Handle quoted content by placing it on its own line
    text = re.sub(r'“([^”]*)”', r'\n“\1”\n', text)  # For curly quotes
    text = re.sub(r'"([^"]*)"', r'\n"\1"\n', text)  # For straight quotes

    # Split text into lines for processing
    lines = text.splitlines()
    processed_lines = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        if buffer:
            buffer += " " + line
        else:
            buffer = line

        # Check if the buffer ends with punctuation and is not part of a quote
        if re.search(r'[.!?]$', buffer) and not re.search(r'[“"”]$', buffer):
            # If there is punctuation within the buffer, split it
            split_buffer = re.split(r'(?<=[.!?])\s+(?![”"])', buffer)  # Avoid splitting inside quotes
            processed_lines.extend(split_buffer)
            buffer = ""

    # Add any remaining text in the buffer
    if buffer:
        processed_lines.append(buffer)

    # Collapse excessive blank lines
    processed_lines = [line for line in processed_lines if line.strip()]
    
    # Collapse excessive spaces
    processed_text = "\n".join(processed_lines)
    processed_text = re.sub(r'[ \t]{2,}', ' ', processed_text)

    # Add final newlines after punctuation for TTS readability
    processed_text = re.sub(r'(?<=[.!?])\s*(?!\n)', '\n', processed_text)

    # Remove excessive blank lines
    processed_text = re.sub(r'\n{3,}', '\n\n', processed_text)

    return processed_text.strip()

def fix_text(text):
    """
    Joins lines that were split due to wrap-around.

    Heuristic:
    - If a line ends with a letter (or letter plus hyphen-like characters) and 
      the next line (after stripping) starts with a lowercase letter, assume 
      the word was cut and join the lines.
    - Remove any trailing hyphen or soft hyphen (U+00AD) before joining.
    """
    lines = text.splitlines()
    fixed_lines = []
    i = 0
    while i < len(lines):
        current_line = lines[i]
        # Continue joining if next line starts with lowercase letter
        while (i < len(lines) - 1 and 
               re.search(r'[\p{L}]$', current_line) and 
               re.match(r'^[a-z]', lines[i+1].lstrip())):
            # Remove trailing hyphen(s) or soft hyphen(s)
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

            filtered_lines.append(text)

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
        # Using raw text (cleaning disabled):
        # chapter_text = clean_text(chapter_text)
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

def save_whole_book(book_name, all_pages_text, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, f"{book_name}_full_text.txt")
    full_text = "\n".join(all_pages_text)
    # Using raw text extraction (cleaning disabled):
    # full_text = clean_text(full_text)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"All content saved to: {output_file}")

def extract_book(pdf_path, use_toc=True, extract_mode="chapters", output_base_dir="extracted_books", progress_callback=None):
    """
    Extract book text from a PDF.
    :param pdf_path: Path to the input PDF file
    :param use_toc: Whether to use TOC if available
    :param extract_mode: "chapters" or "whole"
    :param output_base_dir: Base directory for extraction results
    :return: The output directory containing extracted text files.
    """
    if progress_callback:
        progress_callback(10)
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"File '{pdf_path}' does not exist.")

    doc = fitz.open(pdf_path)
    all_pages_text = extract_cleaned_text(doc)
    toc = get_table_of_contents(doc)
    deduplicated_t = deduplicate_toc(toc)
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Output directory structure: extracted_books/<book_name>/
    output_dir = output_base_dir
    os.makedirs(output_dir, exist_ok=True)

    if use_toc and deduplicated_t and extract_mode == "chapters":
        chapters = structure_text_by_toc(deduplicated_t, all_pages_text)
        save_chapters(chapters, book_name, output_dir)
    else:
        print("Output dir is: ", output_dir)
        save_whole_book(book_name, all_pages_text, output_dir)

    doc.close()
    print("Extraction complete.")
    if progress_callback:
        progress_callback(100)
    return output_dir

# Main block for testing raw text extraction saved into chapters
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    try:
        extract_book(pdf_path, use_toc=True, extract_mode="chapters", output_base_dir="extracted_books")
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)
