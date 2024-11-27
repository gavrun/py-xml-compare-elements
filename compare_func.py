from lxml import etree
import os
import argparse
from collections import defaultdict

# lxml lib for parsing analisys of XML

def parse_with_recovery(file_path):
    # parse an XML file safely with recovery for corrupted files
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(content, parser=parser)
        return root
    except etree.XMLSyntaxError as e:
        print(f"Failed to parse XML: {e}")
        return None # if corrupted

def element_signature(element):
    # create a signature for an element based on its tag, attributes, and clean text
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),  # sort attributes to ensure consistent order
        (element.text or "").strip()  # normalize text by stripping whitespaces
    )

def compare_elements_unordered(element1, element2, differences, matches, path="/"):
    # compare two elements ignoring child elements order
    if element1.tag != element2.tag:
        differences.append(f"Different tags at {path}: '{element1.tag}' != '{element2.tag}'")
        return

    matches.append(f"Matching tags at {path}: '{element1.tag}'") # accumulate results

    # compare attributes
    if element1.attrib != element2.attrib:
        differences.append(f"Different attributes at {path}/{element1.tag}: {element1.attrib} != {element2.attrib}")
    else:
        matches.append(f"Matching attributes at {path}/{element1.tag}: {element1.attrib}")

    # compare children as unordered sets
    children1 = list(element1)
    children2 = list(element2)

    # create sets of child element signatures
    set1 = defaultdict(list)
    set2 = defaultdict(list)

    for child in children1:
        set1[element_signature(child)].append(child)

    for child in children2:
        set2[element_signature(child)].append(child)

    # compare sets, match, diff, missing
    for key in set1.keys() | set2.keys():  # union of keys
        if key not in set2:
            differences.append(f"Missing element in second file at {path}/{element1.tag}: {key}")
        elif key not in set1:
            differences.append(f"Missing element in first file at {path}/{element1.tag}: {key}")
        else:
            # compare occurrences of the element
            count1 = len(set1[key])
            count2 = len(set2[key])
            if count1 != count2:
                differences.append(f"Different count of element {key} at {path}/{element1.tag}: {count1} != {count2}")
            else:
                matches.append(f"Matching element {key} at {path}/{element1.tag}: {count1} occurrences")

    # recursively compare children with matching signatures
    for key in set1.keys() & set2.keys():  # intersection of keys
        for child1, child2 in zip(set1[key], set2[key]):
            compare_elements_unordered(child1, child2, differences, matches, f"{path}/{element1.tag}")
    # not comparing if children do not match

def compare_xml_files(file1, file2):
    # compare the structure of two XML files with detailed child analysis
    root1 = parse_with_recovery(file1)
    root2 = parse_with_recovery(file2)

    if root1 is None or root2 is None:
        print("Failed to parse one or both XML files.")
        return
    # initialize lists for matches and differences
    differences = []
    matches = []
    # compare
    compare_elements_unordered(root1, root2, differences, matches)

    if not differences:
        print("XML structures are identical. Matches have been written to match.txt.")
    else:
        print("XML structures are different. Differences have been written to diff.txt.")

    # write matches to a file
    matches_file = os.path.join(os.path.dirname(__file__), "match.txt")
    with open(matches_file, "w", encoding="utf-8") as f:
        f.write("\n".join(matches))

    # write differences to a file
    if differences:
        differences_file = os.path.join(os.path.dirname(__file__), "diff.txt")
        with open(differences_file, "w", encoding="utf-8") as f:
            f.write("\n".join(differences))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare the structure of two XML files with unordered child comparison.")
    parser.add_argument("file1", help="Path to the first XML file.")
    parser.add_argument("file2", help="Path to the second XML file.")
    args = parser.parse_args()

    compare_xml_files(args.file1, args.file2)
