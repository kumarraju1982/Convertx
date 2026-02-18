"""
Layout Analyzer for detecting document structure from OCR results.

This module analyzes OCR output to identify document structure elements such as
paragraphs, headings, tables, and lists based on text positioning and formatting.
"""

import re
from typing import List, Tuple, Dict, Set
from app.models import OCRResult, DocumentStructure, StructureElement, WordBox


class LayoutAnalyzer:
    """
    Analyzes OCR results to detect document structure.
    
    This class processes OCR output with word-level positioning information
    to identify structural elements like paragraphs, headings, tables, and lists.
    """
    
    def __init__(self):
        """Initialize the Layout Analyzer."""
        pass
    
    def analyze(self, ocr_result: OCRResult) -> DocumentStructure:
        """
        Analyze OCR result to detect document structure.
        
        Processes word-level OCR data to identify:
        - Paragraph boundaries based on vertical spacing
        - Headings based on font size (larger text)
        - Tables based on grid patterns in word positions
        - Lists based on bullet points and numbered items
        - Multi-column layouts
        
        Args:
            ocr_result: OCRResult containing text and word positions
            
        Returns:
            DocumentStructure containing detected structure elements
            
        Requirements:
            - 3.1: Identify paragraph boundaries
            - 3.2: Detect headings based on font size and position
            - 3.3: Identify table structures with rows and columns
            - 3.4: Identify bullet points or numbered lists
            - 3.5: Detect column layout
        """
        if not ocr_result.words:
            # No words detected, return empty structure
            return DocumentStructure(elements=[])
        
        # Group words into lines based on vertical position
        lines = self._group_words_into_lines(ocr_result.words)
        
        # Detect multi-column layout
        columns = self._detect_columns(lines)
        
        # Process each column separately
        all_elements = []
        for column_lines in columns:
            # Detect tables first (they have priority over other structures)
            table_regions = self._detect_table_regions(column_lines)
            
            # Detect structure elements from lines, excluding table regions
            elements = self._detect_structure_elements(column_lines, table_regions)
            all_elements.extend(elements)
        
        return DocumentStructure(elements=all_elements)
    
    def _group_words_into_lines(self, words: List[WordBox]) -> List[List[WordBox]]:
        """
        Group words into lines based on vertical position.
        
        Words with similar y-coordinates are grouped together as a line.
        Lines are sorted from top to bottom.
        
        Args:
            words: List of WordBox objects with position information
            
        Returns:
            List of lines, where each line is a list of WordBox objects
        """
        if not words:
            return []
        
        # Sort words by vertical position (top to bottom), then horizontal (left to right)
        sorted_words = sorted(words, key=lambda w: (w.y, w.x))
        
        lines: List[List[WordBox]] = []
        current_line: List[WordBox] = [sorted_words[0]]
        
        # Threshold for considering words on the same line (pixels)
        # Words within this vertical distance are considered on the same line
        line_threshold = sorted_words[0].height * 0.5
        
        for word in sorted_words[1:]:
            # Check if word is on the same line as the current line
            # Compare with the first word in the current line
            if abs(word.y - current_line[0].y) <= line_threshold:
                current_line.append(word)
            else:
                # Start a new line
                lines.append(current_line)
                current_line = [word]
                line_threshold = word.height * 0.5
        
        # Add the last line
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _detect_columns(self, lines: List[List[WordBox]]) -> List[List[List[WordBox]]]:
        """
        Detect multi-column layouts.
        
        Analyzes horizontal distribution of words to identify if the page
        has multiple columns. Returns lines grouped by column.
        
        Args:
            lines: List of lines, where each line is a list of WordBox objects
            
        Returns:
            List of columns, where each column is a list of lines
            
        Requirements:
            - 3.5: Detect column layout
        """
        if not lines:
            return []
        
        # Calculate the horizontal positions of all lines
        line_x_ranges = []
        for line in lines:
            if line:
                min_x = min(word.x for word in line)
                max_x = max(word.x + word.width for word in line)
                line_x_ranges.append((min_x, max_x, line))
        
        if not line_x_ranges:
            return [lines]
        
        # Find potential column boundaries
        # Look for consistent gaps in horizontal distribution
        all_x_positions = []
        for min_x, max_x, _ in line_x_ranges:
            all_x_positions.extend([min_x, max_x])
        
        # Calculate page width
        page_left = min(all_x_positions)
        page_right = max(all_x_positions)
        page_width = page_right - page_left
        
        # Check if there's a consistent vertical gap (column separator)
        # Sample x-positions across the page
        gap_threshold = page_width * 0.1  # 10% of page width
        
        # Count how many lines have content at each x-position
        x_coverage = {}
        for x in range(int(page_left), int(page_right), 5):  # Sample every 5 pixels
            coverage_count = 0
            for min_x, max_x, _ in line_x_ranges:
                if min_x <= x <= max_x:
                    coverage_count += 1
            x_coverage[x] = coverage_count
        
        # Find gaps (positions with low coverage)
        gaps = []
        for x, count in x_coverage.items():
            if count < len(lines) * 0.2:  # Less than 20% of lines have content here
                gaps.append(x)
        
        # Find continuous gap regions
        gap_regions = []
        if gaps:
            current_gap_start = gaps[0]
            current_gap_end = gaps[0]
            
            for gap_x in gaps[1:]:
                if gap_x - current_gap_end <= 10:  # Continuous gap
                    current_gap_end = gap_x
                else:
                    if current_gap_end - current_gap_start >= gap_threshold:
                        gap_regions.append((current_gap_start, current_gap_end))
                    current_gap_start = gap_x
                    current_gap_end = gap_x
            
            # Add last gap
            if current_gap_end - current_gap_start >= gap_threshold:
                gap_regions.append((current_gap_start, current_gap_end))
        
        # If no significant gaps found, treat as single column
        if not gap_regions:
            return [lines]
        
        # Split lines into columns based on gaps
        # For simplicity, use the first major gap as column separator
        separator_x = (gap_regions[0][0] + gap_regions[0][1]) / 2
        
        left_column = []
        right_column = []
        
        for line in lines:
            if line:
                line_center = sum(word.x + word.width / 2 for word in line) / len(line)
                if line_center < separator_x:
                    left_column.append(line)
                else:
                    right_column.append(line)
        
        # Return non-empty columns
        columns = []
        if left_column:
            columns.append(left_column)
        if right_column:
            columns.append(right_column)
        
        return columns if columns else [lines]
    
    def _detect_table_regions(self, lines: List[List[WordBox]]) -> List[Tuple[int, int]]:
        """
        Detect table regions based on grid patterns.
        
        Identifies sequences of lines that form a grid pattern with
        consistent column alignment. Excludes lines that are list items.
        
        Args:
            lines: List of lines, where each line is a list of WordBox objects
            
        Returns:
            List of (start_index, end_index) tuples indicating table regions
            
        Requirements:
            - 3.3: Identify table structures with rows and columns
        """
        if len(lines) < 3:  # Need at least 3 rows for a table
            return []
        
        table_regions = []
        i = 0
        
        while i < len(lines):
            # Skip lines that are list items (they shouldn't be part of tables)
            line_text = ' '.join(word.text for word in lines[i]) if lines[i] else ""
            if self._is_list_item(line_text)[0]:
                i += 1
                continue
            
            # Check if current position starts a table
            table_end = self._find_table_end(lines, i)
            
            if table_end > i + 2:  # Found a table with at least 3 rows
                table_regions.append((i, table_end))
                i = table_end
            else:
                i += 1
        
        return table_regions
    
    def _find_table_end(self, lines: List[List[WordBox]], start: int) -> int:
        """
        Find the end of a table starting at the given line index.
        
        Args:
            lines: List of lines
            start: Starting line index
            
        Returns:
            End line index (exclusive) or start if no table found
        """
        if start >= len(lines) - 2:
            return start
        
        # Analyze column alignment for consecutive lines
        # Extract x-positions of words in each line
        line_columns = []
        for i in range(start, min(start + 10, len(lines))):  # Look ahead up to 10 lines
            line = lines[i]
            if not line:
                break
            
            # Get x-positions of words (left edge)
            x_positions = sorted([word.x for word in line])
            
            # Tables should have multiple words per line (at least 2 columns)
            if len(x_positions) < 2:
                if i == start:
                    return start  # First line doesn't have enough columns
                break
            
            line_columns.append(x_positions)
        
        if len(line_columns) < 3:
            return start
        
        # Check for consistent column alignment
        # Find common x-positions across lines (with tolerance)
        tolerance = 15  # pixels
        
        # Get all unique x-positions
        all_x = set()
        for positions in line_columns:
            all_x.update(positions)
        
        # Cluster x-positions into columns
        columns = self._cluster_positions(list(all_x), tolerance)
        
        # Need at least 2 columns for a table
        if len(columns) < 2:
            return start
        
        # Check how many lines have words at EACH column position
        # For a true table, most columns should appear in most rows
        column_appearances = [0] * len(columns)
        for positions in line_columns:
            for col_idx, col_x in enumerate(columns):
                # Check if this line has a word near this column
                for x in positions:
                    if abs(x - col_x) <= tolerance:
                        column_appearances[col_idx] += 1
                        break
        
        # Check if columns are consistently used across rows
        # At least 80% of rows should have content in at least 80% of columns
        min_column_usage = len(line_columns) * 0.8
        columns_with_good_usage = sum(1 for count in column_appearances if count >= min_column_usage)
        
        if columns_with_good_usage < len(columns) * 0.8:
            return start  # Not enough consistent column usage
        
        # Check how many lines align with these columns
        aligned_count = 0
        for positions in line_columns:
            # Check if this line's words align with the detected columns
            aligned_words = 0
            for x in positions:
                for col_x in columns:
                    if abs(x - col_x) <= tolerance:
                        aligned_words += 1
                        break
            
            # If most words align (at least 70%), consider this line part of the table
            if len(positions) > 0 and aligned_words / len(positions) >= 0.7:
                aligned_count += 1
            else:
                # Line doesn't align, table ends here
                break
        
        # Need at least 3 aligned lines and at least 2 columns
        # Also check that lines have similar number of words (table characteristic)
        if aligned_count >= 3 and len(columns) >= 2:
            # Additional check: lines should have similar word counts
            word_counts = [len(positions) for positions in line_columns[:aligned_count]]
            avg_word_count = sum(word_counts) / len(word_counts)
            
            # Check if word counts are consistent (within 50% of average)
            consistent_count = sum(1 for count in word_counts if abs(count - avg_word_count) <= avg_word_count * 0.5)
            
            # At least 70% of lines should have consistent word counts
            if consistent_count / len(word_counts) >= 0.7:
                return start + aligned_count
        
        return start
    
    def _cluster_positions(self, positions: List[float], tolerance: float) -> List[float]:
        """
        Cluster positions that are close together.
        
        Args:
            positions: List of positions to cluster
            tolerance: Maximum distance between positions in same cluster
            
        Returns:
            List of cluster centers
        """
        if not positions:
            return []
        
        sorted_pos = sorted(positions)
        clusters = [[sorted_pos[0]]]
        
        for pos in sorted_pos[1:]:
            # Check if close to last cluster
            if pos - clusters[-1][-1] <= tolerance:
                clusters[-1].append(pos)
            else:
                clusters.append([pos])
        
        # Return cluster centers (average of positions in cluster)
        return [sum(cluster) / len(cluster) for cluster in clusters]
    
    def _is_list_item(self, line_text: str) -> Tuple[bool, str]:
        """
        Check if a line is a list item (bullet or numbered).
        
        Args:
            line_text: Text content of the line
            
        Returns:
            Tuple of (is_list_item, list_type) where list_type is "bullet" or "numbered"
            
        Requirements:
            - 3.4: Identify bullet points or numbered lists
        """
        line_text = line_text.strip()
        
        if not line_text:
            return False, ""
        
        # Check for bullet points (•, -, *, ○, ■, etc.)
        bullet_patterns = [
            r'^[•\-\*○■□▪▫][\s]',  # Common bullet characters
            r'^[\u2022\u2023\u2043\u204C\u204D\u2219\u25AA\u25AB\u25CF\u25E6][\s]',  # Unicode bullets
        ]
        
        for pattern in bullet_patterns:
            if re.match(pattern, line_text):
                return True, "bullet"
        
        # Check for numbered lists (1., 1), a., a), i., etc.)
        numbered_patterns = [
            r'^\d+[\.\)][\s]',  # 1. or 1)
            r'^[a-z][\.\)][\s]',  # a. or a)
            r'^[A-Z][\.\)][\s]',  # A. or A)
            r'^[ivxlcdm]+[\.\)][\s]',  # Roman numerals (lowercase)
            r'^[IVXLCDM]+[\.\)][\s]',  # Roman numerals (uppercase)
        ]
        
        for pattern in numbered_patterns:
            if re.match(pattern, line_text):
                return True, "numbered"
        
        return False, ""
    
    def _extract_table_structure(self, lines: List[List[WordBox]], start: int, end: int) -> StructureElement:
        """
        Extract table structure from a region of lines.
        
        Args:
            lines: List of all lines
            start: Start index of table region
            end: End index of table region (exclusive)
            
        Returns:
            StructureElement representing the table
        """
        table_lines = lines[start:end]
        
        # Extract text from each row
        rows = []
        for line in table_lines:
            row_text = ' '.join(word.text for word in line)
            rows.append(row_text)
        
        # Combine rows with newlines
        table_content = '\n'.join(rows)
        
        # Detect number of columns by analyzing alignment
        all_x = []
        for line in table_lines:
            for word in line:
                all_x.append(word.x)
        
        columns = self._cluster_positions(all_x, tolerance=15)
        
        return StructureElement(
            type="table",
            content=table_content,
            style={"rows": len(table_lines), "columns": len(columns)}
        )
    
    def _detect_structure_elements(self, lines: List[List[WordBox]], table_regions: List[Tuple[int, int]] = None) -> List[StructureElement]:
        """
        Detect structure elements from grouped lines.
        
        Analyzes lines to identify:
        - Headings: Lines with larger font size (height)
        - Paragraphs: Groups of lines with consistent spacing
        - Lists: Lines starting with bullets or numbers
        - Tables: Grid patterns (handled separately)
        
        Args:
            lines: List of lines, where each line is a list of WordBox objects
            table_regions: List of (start, end) tuples indicating table regions to skip
            
        Returns:
            List of StructureElement objects
        """
        if not lines:
            return []
        
        if table_regions is None:
            table_regions = []
        
        # Create a set of line indices that are part of tables
        table_line_indices = set()
        for start, end in table_regions:
            table_line_indices.update(range(start, end))
        
        elements: List[StructureElement] = []
        
        # Calculate average line height for comparison
        # Use the maximum height in each line to represent the line's font size
        line_heights = [max(word.height for word in line) for line in lines if line]
        avg_height = sum(line_heights) / len(line_heights) if line_heights else 0
        
        # Threshold for detecting headings (lines with larger text)
        # Text 1.14x larger than average is considered a heading
        heading_threshold = avg_height * 1.14
        
        # First, add table elements
        for start, end in table_regions:
            table_element = self._extract_table_structure(lines, start, end)
            elements.append(table_element)
        
        # Process each line (skipping table regions)
        i = 0
        while i < len(lines):
            # Skip if this line is part of a table
            if i in table_line_indices:
                i += 1
                continue
            
            line = lines[i]
            if not line:
                i += 1
                continue
            
            line_height = max(word.height for word in line)
            line_text = ' '.join(word.text for word in line)
            
            # Check if this line is a heading (larger text)
            if line_height >= heading_threshold:
                # Determine heading level based on relative size
                # Larger text = higher level (lower number)
                if line_height >= avg_height * 1.8:
                    level = 1
                elif line_height >= avg_height * 1.5:
                    level = 2
                else:
                    level = 3
                
                elements.append(StructureElement(
                    type="heading",
                    content=line_text,
                    level=level,
                    style={"font_size": line_height}
                ))
                i += 1
            else:
                # Check if this is a list item
                is_list, list_type = self._is_list_item(line_text)
                
                if is_list:
                    # Collect consecutive list items
                    list_items = [line_text]
                    i += 1
                    
                    while i < len(lines) and i not in table_line_indices:
                        next_line = lines[i]
                        if not next_line:
                            break
                        
                        next_height = max(word.height for word in next_line)
                        next_text = ' '.join(word.text for word in next_line)
                        
                        # Stop if next line is a heading
                        if next_height >= heading_threshold:
                            break
                        
                        # Check if next line is also a list item of the same type
                        next_is_list, next_list_type = self._is_list_item(next_text)
                        if next_is_list and next_list_type == list_type:
                            list_items.append(next_text)
                            i += 1
                        else:
                            break
                    
                    # Create list element
                    list_content = '\n'.join(list_items)
                    elements.append(StructureElement(
                        type="list",
                        content=list_content,
                        style={"list_type": list_type}
                    ))
                else:
                    # This is regular text, group consecutive lines into a paragraph
                    paragraph_lines = [line_text]
                    i += 1
                    
                    # Look ahead to group lines into paragraph
                    while i < len(lines) and i not in table_line_indices:
                        next_line = lines[i]
                        if not next_line:
                            break
                        
                        next_height = max(word.height for word in next_line)
                        next_text = ' '.join(word.text for word in next_line)
                        
                        # Stop if next line is a heading
                        if next_height >= heading_threshold:
                            break
                        
                        # Stop if next line is a list item
                        if self._is_list_item(next_text)[0]:
                            break
                        
                        # Calculate vertical spacing between lines
                        prev_line = lines[i - 1]
                        prev_bottom = max(word.y + word.height for word in prev_line)
                        next_top = min(word.y for word in next_line)
                        spacing = next_top - prev_bottom
                        
                        # If spacing is large (more than 1.5x average line height), start new paragraph
                        # This detects paragraph boundaries based on vertical spacing
                        if spacing > avg_height * 1.5:
                            break
                        
                        # Add line to current paragraph
                        paragraph_lines.append(next_text)
                        i += 1
                    
                    # Create paragraph element
                    paragraph_text = '\n'.join(paragraph_lines)
                    elements.append(StructureElement(
                        type="paragraph",
                        content=paragraph_text,
                        style={}
                    ))
        
        return elements
