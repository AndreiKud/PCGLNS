import sys
import os
from pathlib import Path


def get_line_contains_idx(substr, lines):
    idx = -1
    for line in lines:
        if line.startswith(substr):
            idx = lines.index(line)
    
    return idx


def convert_wight_section(text):
    orderings = []
    lines = text.split("\n")
    idx = get_line_contains_idx("EDGE_WEIGHT_SECTION", lines)
    dims_idx = get_line_contains_idx("DIMENSION", lines)
    sets_idx = get_line_contains_idx("GTSP_SETS", lines)

    if idx == -1 or dims_idx == -1:
        return text, orderings

    dims = int(lines[dims_idx].split(" : ")[1])
    for i in range(idx + 1, idx + dims + 1):
        # tmptmp = ().split(" ")
        # print(tmptmp)
        # for tmp1 in tmptmp:
        #     print(tmp1)
        #     print(float(tmp1))
        # float_str = lines[i].strip().replace(".", ",")
        float_lst = list(map(float, lines[i].strip().split(" ")))
        tmplst = []
        for vert_idx, fl in enumerate(float_lst):
            if fl == -1:
                tmplst.append(vert_idx + 1)
        
        orderings.append(tmplst)
    
    return "\n".join(lines), orderings


def add_sets_ordering_section(lines, orderings):
    idx = get_line_contains_idx("GTSP_SETS", lines)
    if idx == -1:
        return text
    sets_num = int(lines[idx].split(" : ")[1])
    
    idx = get_line_contains_idx("GTSP_SET_SECTION", lines)
    if idx == -1:
        return text
    
    sets = []
    for set_line_idx in range(idx + 1, idx + sets_num + 1):
        set_vals = []
        splitted = lines[set_line_idx].split(" ")[:-1]
        set_idx = int(splitted[0])
        for set_val in splitted[1:]:
            set_vals.append(int(set_val))
        sets.append(set_vals)
    # print(sets)
    # print(orderings)


    idx = get_line_contains_idx("EOF", lines)
    if idx == -1:
        return text
    
    # inverted_orderings = [None] * sets_num
    inverted_orderings = []
    for ord_idx, ordering in enumerate(orderings):
        if ordering:
            src_idx = -1
            for inner_idx, set_to_precede in enumerate(sets):
                if ord_idx + 1 in set_to_precede:
                    src_idx = inner_idx + 1
                    break
            
            if src_idx == -1:
                print("Failed to find src set")
                break
            
            # inverted_orderings
            ordering_tmp = []
            set_to_insert = set()
            for set_from in ordering:
                dst_idx = -1
                for inner_idx, set_to_precede in enumerate(sets):
                    if set_from in set_to_precede:
                        dst_idx = inner_idx
                        break
                if dst_idx == -1:
                    print("Failed to find dst set")
                    break
                set_to_insert.add(dst_idx + 1)
            
            ordering_tmp.append(src_idx)
            ordering_tmp.append(list(set_to_insert))
            if ordering_tmp not in inverted_orderings:
                inverted_orderings.append(ordering_tmp)
    
    # print(sets, "\n")
    # print(orderings, "\n")
    # print(inverted_orderings, "\n")

    final_ordering = []
    for ord_idx, ordering in enumerate(inverted_orderings):
        if not ordering:
            continue
        
        for set_idx in ordering[1]:
            sets_set = set()
            for inner_ordering in inverted_orderings:
                if set_idx in inner_ordering[1]:
                    sets_set.add(inner_ordering[0])
            
            new_lst = [set_idx, list(sets_set)]
            if new_lst not in final_ordering:
                final_ordering.append(new_lst)
    
    # print(final_ordering)
    
    lines.insert(idx, "GTSP_SET_ORDERING")
    next_line_idx = 1
    for ordering in final_ordering:
        if ordering:
            ordering_str = str(ordering[0])
            for set_idx in ordering[1]:
                ordering_str = ordering_str + str(" " + str(set_idx))
            ordering_str = ordering_str + str(" -1")
            # print(idx, " ", next_line_idx)
            lines.insert(idx + next_line_idx, ordering_str)
            next_line_idx = next_line_idx + 1

    return lines


def remove_pc_specific_param(param_name, text_lines):
    idx = get_line_contains_idx(param_name, text_lines)
    if idx != -1:
        del text_lines[idx + 1]
        del text_lines[idx]

    return text_lines


def remove_params(text):
    lines = text.split("\n")
    lines = remove_pc_specific_param("NODE_WEIGHT_SECTION", lines)
    lines = remove_pc_specific_param("START_GROUP_SECTION", lines)
    lines = remove_pc_specific_param("NODE_AGENT_SECTION", lines)
    
    return "\n".join(lines)


def rename_params(text):
    text = text.replace("GROUPS :", "GTSP_SETS :")
    text = text.replace("NODE_GROUP_SECTION", "GTSP_SET_SECTION")
    
    return text


def set_params(text):
    text, orderings = convert_wight_section(text)
    lines = text.split("\n")
    idx = get_line_contains_idx("TYPE", lines)
    if idx == -1:
        return
    
    lines[idx] = lines[idx].split(" : ")[0] + " : PCGLNS"

    idx = get_line_contains_idx("NAME", lines)
    if idx == -1:
        return

    paramName = lines[idx].split(" : ")[0]
    fullName = lines[idx].split(" : ")[1]
    lines[idx] = paramName + " : " + fullName.split(".")[0] + ".pcglns"

    lines = add_sets_ordering_section(lines, orderings)

    return "\n".join(lines)



def convert_text(origin):
    converted = origin
    converted = converted.replace(":", " :")
    converted = converted.replace("  ", " ")

    converted = remove_params(converted)
    converted = rename_params(converted)
    converted = set_params(converted)

    return converted


def convert_file(input_dir, filename, output_dir):
    if not filename.endswith(".pcgtsp"):
        return
    
    pcgtsp_file = open(input_dir + filename, "r")
    text = pcgtsp_file.read()
    converted = convert_text(text)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    gtsp_file_name = os.path.splitext(filename)[0] + ".pcglns"
    gtsp_file = open(output_dir + gtsp_file_name, "w+")
    gtsp_file.write(converted)
    gtsp_file.close()


def convert_dir(input, output_dir):
    for filename in os.listdir(input):
        print("Processing " + filename + "...")
        convert_file(input, filename, output_dir)


if __name__ == "__main__":
    argc = len(sys.argv)
    if argc < 2 or argc > 3:
        print(f"Wrong arguments number")
        exit(0)
    
    input = sys.argv[1]
    is_dir = os.path.isdir(input)
    if is_dir and not input.endswith('/'):
        input = input + '/'
    
    output_dir = ""
    if argc == 3:
        output_dir = sys.argv[2]
        if not output_dir.endswith('/'):
            output_dir = output_dir + "/"
    
    if is_dir:
        convert_dir(input, output_dir)
    else:
        convert_file("", input, output_dir)