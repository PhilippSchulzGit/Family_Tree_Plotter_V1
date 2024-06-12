# -*- coding: utf-8 -*-
"""
Python script to visualize a family tree. The source data is contained inside
an Excel sheet that lists a person with:
ID, first name(s), last name (at birth), birth date, birth location, death date,
death location,  of mother, ID of father, ID of wedding, IDs of children, gender,
tree color, flag for still alive
This script tries to plot all people into one large file.

@author: Philipp Schulz
"""
import graphviz
import excel_parser

path = "Stammbaum_anonymous_small.xlsx"  # define path and filename for Excel file with family tree data
path = "Stammbaum_anonymous_small2.xlsx"  # define path and filename for Excel file with family tree data
# path = "Stammbaum_anonymous_medium.xlsx"  # define path and filename for Excel file with family tree data
# path = "Stammbaum_anonymous.xlsx"  # define path and filename for Excel file with family tree data
dot_node_size = str(0.08)  # size of the small dot that is plotted between two people
graph_attributes={'splines': "ortho", 'nodesep':'0.75',  'ranksep': '0.5', 'overlap':'false',
            'newrank':'true', 'concentrate': 'false'}
graph_attributes2={"rank": "same", "newrank": "true"}
node_attributes={'style': 'filled', 'shape': 'box',"label":"\\N"}
edge_attributes={'dir': 'none', 'arrowhead': 'none', "penwidth":"3"}

def parse_excel_data(excel_path):
    """
    Reads content from Excel file and parses it into a usable format.
    @param excel_path: Relative path to the Excel file.
    @return: Data from Excel file as a large list.
    """
    # read data from file
    family_tree_data = excel_parser.read_excel_content(path)
    # filter out "None" fields, replace with ""
    for i in range(0,len(family_tree_data)-1, 1):
        for j in range(0, len(family_tree_data[i]), 1):
            for k in range(0, len(family_tree_data[i][j]),1):
                if family_tree_data[i][j][k] == "None":
                    family_tree_data[i][j][k] = ""
    # add a field that indicates the hierarchy of that person
    family_tree_data[0].append([0 for i in range(0,len(family_tree_data[0][0]),1)])
    family_tree_data[0][-1][0] = "Hierarchy"
    # crop date fields to remove time and only leave date # 3, 5, 3
    family_tree_data[0][3] = [family_tree_data[0][3][i].split(" ")[0] for i in range(0,len(family_tree_data[0][3]),1)]
    family_tree_data[0][5] = [family_tree_data[0][5][i].split(" ")[0] for i in range(0,len(family_tree_data[0][3]),1)]
    family_tree_data[1][3] = [family_tree_data[1][3][i].split(" ")[0] for i in range(0,len(family_tree_data[1][3]),1)]
    return family_tree_data  # return list with data


def generate_flat_list(data):
    """
    Generates a flat list for all people from the Excel data.
    @param data: Family tree data read from Excel file.
    @return: flat list with entries for each person.
    """
    flat_list = []  # initialize return value
    for i in range(1, len(data[0][0]), 1):  # loop over all people
        flat_list.append([data[0][j][i] for j in range(0, len(data[0])-1, 1)])
        flat_list[-1][0] = int(flat_list[-1][0])  # convert own id to int
        flat_list[-1][7] = [int(flat_list[-1][7])] if "-" not in flat_list[-1][7] and len(flat_list[-1][7])>0 else []  # convert mother id to int
        flat_list[-1][8] = [int(flat_list[-1][8])] if "-" not in flat_list[-1][8] and len(flat_list[-1][8])>0 else []  # convert father id to int
        # convert child ids to int list
        flat_list[-1][10] = [int(child) for child in flat_list[-1][10].replace("-","").split(",") if len(child) > 0]
        flat_list[-1][9] = []  # initialize spouses as numeric list
    for i in range(0, len(flat_list), 1):  # populate spouse ids
        for j in range(1, len(data[1][0]), 1):  # loop over all spouses
            if int(flat_list[i][0]) == int(data[1][1][j]):  # add spouse 1
                flat_list[i][9].append(int(data[1][2][j]))
            elif int(flat_list[i][0]) == int(data[1][2][j]):  # add spouse 2
                flat_list[i][9].append(int(data[1][1][j]))
    return flat_list


def insert_into_flat_cluster(person, cluster):
    """
    Inserts a new person into the given cluster recursively.
    @param person: Local cluster of the currently active person.
    @cluster: Currently active cluster the person shall be inserted into.
    @return: New cluster with new person included, flag to indicate success.
    """
    new_cluster, flag = cluster.copy(), False  # initialize new cluster and flag
    # step 1: check people directly
    for i in range(1, 3, 1):  # check mother and father directly
        if new_cluster[i] and not flag:  # check if there is an entry and if the flag is not set
            if type(new_cluster[i][0]) != list:  # if this entry is not a cluster
                if person[0] == new_cluster[i][0]:  # if the ids are identical
                    new_cluster[i][0] = person  # assign person to cluster
                    flag = True  # set flag
    for h in range(4, 2, -1):  # check children and spouses directly
        if flag:  # skip rest if flag is set
            break
        for i, entry in enumerate(new_cluster[h]):  # check people directly
            if entry and not flag:  # check if there is an entry and if the flag is not set
                if type(entry) != list:  # if this entry is not a cluster
                    if person[0] == entry:  # if the ids are identical
                        new_cluster[h][i] = person  # assign person to cluster
                        flag = True  # set flag
            elif flag:  # exit loop if flag is set
                break
    # check parents, children and spouses recursively
    for i, category in enumerate(new_cluster[1:]):  # loop over all entries
        if flag:  # check exit condition
            break
        for j, entry in enumerate(category):  # loop over all indices in current category
            if flag:  # check exit condition
                break
            if type(entry) == list:  # check if current entry is not a cluster
                # recursive call
                new_cluster[i+1][j], flag = insert_into_flat_cluster(person, entry)
    return new_cluster, flag  # return the potentially updated cluster and the flag


def generate_flat_master_cluster(flat_list):
    """
    Converts the flat list of all people into a flat list of cluster data.
    @param flat_list: Flat list of all people with all data from Excel file.
    @return: Flat list containing cluster-relevant data for all people.
    """
    # initialize list to indicate if the person was found + return value
    person_found, cluster = [False for _ in range(0, len(flat_list), 1)], []
    for i, person in enumerate(flat_list):  # loop over all people
        # generate entry for current person: self, mother, father, spouses, children
        current = [person[0], person[7], person[8], person[9], person[10]]
        if not cluster:  # handle first cycle
            cluster = current  # assign current node as cluster root
            person_found[i] = True
        else:  # applies for all other cases
            cluster, person_found[i] = insert_into_flat_cluster(current, cluster)
    # sometimes the order of parents and children is swapped. Go over list again
    person_found_prev, flag = person_found.copy(), True
    while flag:  # loop until flag is reset
        for i, person in enumerate(flat_list):  # loop over all people
            if not person_found[i]:  # check if current person was already found
                # generate entry for current person: self, mother, father, spouses, children
                current = [person[0], person[7], person[8], person[9], person[10]]
                # try to fit current person into cluster
                cluster, person_found[i] = insert_into_flat_cluster(current, cluster)
        if person_found == person_found_prev or False not in person_found:
            flag = False  # exit the loop due to either no change or all people found
        person_found_prev = person_found.copy()  # copy list for next loop
    return cluster  # return value


# https://stackoverflow.com/questions/71571613/implement-family-tree-visualization-in-graphviz
def add_child_node(tree, parent1, parent2, child, person_plotted, flat_list):
    """
    Adds a child node to a given tree. Adds parents if they miss.
    @param tree: Tree to which the parents and children shall be added to.
    @param parent1: First parent of the children.
    @param parent2: Second parent of the children.
    @param child: Child to add.
    @param person_plotted: Internal flag used to indicate whether a person exists on the tree.
    @param flat_list: List that contains all data for all people to fetch via ID.
    @return: Updated version of input parameter person_plotted.
    """
    # step 1: get all children of the parents
    children1 = [] if not parent1 else [child for child in parent1[10]]
    for i, child in enumerate(children1):
        if type(child) != int:
            children1[i] = child[0]
    children2 = [] if not parent2 else [child for child in parent2[10]]
    for i, child in enumerate(children2):
        if type(child) != int:
            children2[i] = child[0]    
    if parent1 and parent2:
        children = [flat_list[child_id] for child_id in children1 if child_id in children2]
    else:
        children = [flat_list[c] for c in children1] if parent1 else [flat_list[c] for c in children2]
    # sort children by ages, oldest first
    children = sorted(children, key=lambda x: int(x[3].replace("~","").split("-")[0]+"0"))
    # step 2:  add parent nodes if not already present
    person_plotted, parent_node = add_spouse_node(tree, parent1, parent2, person_plotted)
    p1_id = -1 if not parent1 else parent1[0]
    p2_id = -1 if not parent2 else parent2[0]
    # step 3: add parent_children point nodes
    with tree.subgraph(graph_attr=graph_attributes2) as sub_tree:
        for child in children:
            parent_child_node = f"N{p1_id}_{p2_id}_{child[0]}"
            sub_tree.node(parent_child_node, shape="point", **{"width": dot_node_size})
        if len(children) % 2 == 0:
            center_node = f"N{p1_id}_{p2_id}B"
            sub_tree.node(center_node, shape="point", **{"width": dot_node_size})
    # step 4: connect parent nodes to middle parent_children point or a new center point
    if len(children) % 2 == 0:
        tree.edge(parent_node, center_node)
    else:
        middle_child = children[len(children) // 2]
        parent_child_node = f"N{p1_id}_{p2_id}_{middle_child[0]}"
        # tree.node(middle_child[0], middle_child[1])
        tree.edge(parent_node, parent_child_node)
    # step 5: connect parent_children nodes horizontally
    for i in range(0, len(children)-1, 1):
        parent_child_node1 = f"N{p1_id}_{p2_id}_{children[i][0]}"
        parent_child_node2 = f"N{p1_id}_{p2_id}_{children[i+1][0]}"
        if len(children) % 2 == 0 and i == len(children)/2 - 1:
            tree.edge(parent_child_node1, center_node)
            tree.edge(center_node, parent_child_node2)
        else:
            tree.edge(parent_child_node1, parent_child_node2)
    attr = graph_attributes2.copy()
    attr["peripheries"] = "0"
    # step 6: add children and connect them to their parent_child nodes
    with tree.subgraph(graph_attr=attr) as sub_tree:
        for i, child in enumerate(children):
            parent_child_node = f"N{p1_id}_{p2_id}_{child[0]}"
            if not person_plotted[child[0]]:  # check if child node does not exist
                label, args = generate_node_arguments(child)
                sub_tree.node(str(child[0]), label, **args)  # draw child node
                person_plotted[child[0]] = True  # set flag
            tree.edge(parent_child_node, str(child[0]))
    return person_plotted  # return value


def generate_node_arguments(person):
    """
    Helper function to generate the node arguments for the specified person.
    @param person: Person for which the arguments shall be generated.
    @return: Text label and arguments for the person node.
    """
    birth = "?" if len(person[3]) < 4 else person[3]  # generate birth string
    death = person[5]  # generate death string
    if len(death) < 4 and person[12]:
        death = "today" if person[12] else "?"
    # generate HTML-based labels for people nodes
    full_name = f"{person[1]} {person[2]}"
    if len(full_name) > 22:
        # figure out where to split the name
        split_index = 22
        while(full_name[split_index] != " "):
            split_index -= 1
        name1 = full_name[0:split_index]
        name2 = full_name[split_index:]
        # handle long names
        label = f"<{name1}<BR/>{name2}<BR/><FONT POINT-SIZE=\"9\">"
        label += f"{birth} - {death}</FONT><BR/><FONT POINT-SIZE=\"5\"> </FONT><BR ALIGN=\"CENTER\"/>>"
    else:
        label = f"<{person[1]} {person[2]}<BR/><BR/><FONT POINT-SIZE=\"9\">{birth}"
        label += f" - {death}</FONT><BR/><FONT POINT-SIZE=\"5\"> </FONT><BR ALIGN=\"CENTER\"/>>"
    # add constant node arguments
    node_arguments = {"height":str(2.6), "width":str(2), "penwidth":str(3),
                      "fixedsize":"true", "imagepos":"tc", "imagescale":"true",
                      "labelloc":"bc", "group":f"G{person[0]}"}
    # add node color and default image based on gender
    node_arguments["fillcolor"] = "#C2EBED" if person[11] == "m" else "#F4C2C2"
    node_arguments["image"] = "Images/man.png" if person[11] == "m" else "Images/woman.png"
    return label, node_arguments  # return the node label and additional arguments


# https://stackoverflow.com/questions/71571613/implement-family-tree-visualization-in-graphviz
def add_spouse_node(tree, person1, person2, person_plotted):
    """
    Adds a spouse and the connection between spouses to the current tree.
    @param tree: Currently active tree.
    @param person1: Person 1 of the relationship.
    @param person2: Person 2 of the relationship.
    @param person_plotted: Helper flags to indicate whether a person exists on the tree.
    @return: Updated version of person_plotted, name of the extra node.
    """
    # TODO: HANDLE SINGLE PARENT
    attr = graph_attributes2.copy()
    attr["peripheries"] = "0"
    p1_id = -1 if not person1 else person1[0]
    p2_id = -1 if not person2 else person2[0]
    # generate a sub graph for spouse pair
    with tree.subgraph(name=f"cluster_{p1_id}_{p2_id}", graph_attr = attr) as sub_tree:
        # generate labels and node arguments
        if person1 and not person_plotted[person1[0]]:  # check if person 1 exists on graph
                label1, arguments1 = generate_node_arguments(person1)
                sub_tree.node(str(person1[0]), label1, **arguments1)
                person_plotted[person1[0]] = True
        if person2 and not person_plotted[person2[0]]:  # check if person 2 exists on graph
            label2, arguments2 = generate_node_arguments(person2)
            sub_tree.node(str(person2[0]), label2, **arguments2)
            person_plotted[person2[0]] = True
        # add node that connects both people. Important for children
        node_name = f"N{p1_id}_{p2_id}"
        sub_tree.node(node_name, shape="point", **{"width":str(0.08)})
        # generate edges between people nodes and connector node
        if person1:
            sub_tree.edge(str(person1[0]), node_name)
        if person2:
            sub_tree.edge(node_name, str(person2[0]))
    return person_plotted, node_name  # return list of plotted people and extra node name


def plot_next_person(flat_list, tree, cluster_flat, person_plotted, person_parsed):
    """
    Recursive function to add the next person from a flat list to a given cluster.
    @param flat_list: Flat list containing all people that shall be added to the cluster.
    @param tree: Currently active tree.
    @param cluster_flat: Flat list containing all cluster-relevant data.
    @param person_plotted: Helper flag to indicate whether a person has been added to the tree.
    @param person_parsed: Helper flag to indicate whether a person has been recursively called via this function.
    @return: Updated version of person_plotted.
    """
    if type(cluster_flat) == int:  # handle szenario where cluster is only one index
        if not person_parsed[cluster_flat]:  # set flag to true if not alredy
            person_parsed[cluster_flat] = True
        return person_plotted  # return before rest of code
    if cluster_flat[3]:  # check if current person has any spouses
        for spouse in cluster_flat[3]:  # add all spouses as new nodes
            if type(spouse) != list:
                spouse = [spouse]
            if person_plotted[spouse[0]]:  # skip already plotted people
                continue
            # generate person information lists
            person1 = flat_list[cluster_flat[0]]
            person2 = flat_list[spouse[0]]
            # add the spouse node
            person_plotted, _ = add_spouse_node(tree, person1, person2, person_plotted)
    if cluster_flat[4]:  # check if current person has any children
        for child in cluster_flat[4]:  # add all children as new nodes
            if type(child) != list:
                child = [child, [-1], [-1]]
            if person_plotted[child[0]]:  # skip already plotted people
                continue
            # generate person information lists
            try:
                parent1 = flat_list[child[1][0][0]]
            except:
                if child[1] == []:
                    child[1] = [-1]
                parent1 = flat_list[child[1][0]]
            try:
                parent2 = flat_list[child[2][0][0]]
            except:
                if child[2] == []:
                    child[2] = [-1]
                parent2 = flat_list[child[2][0]]
            # add the child node
            person_plotted = add_child_node(tree, parent1, parent2, child, person_plotted, flat_list)
    if cluster_flat[1] or cluster_flat[2]:  # check if current person has parents
        parent1, parent2, parent_index1, parent_index2 = [], [], -1, -1
        if type(cluster_flat[1]) != list:
            cluster_flat[1] = [[cluster_flat[1]]]
        if type(cluster_flat[2]) != list:
            cluster_flat[2] = [[cluster_flat[2]]]
        if cluster_flat[1]:
            parent_index1 = cluster_flat[1][0] if type(cluster_flat[1][0]) == int else cluster_flat[1][0][0]
        if cluster_flat[2]:
            parent_index2 = cluster_flat[2][0] if type(cluster_flat[2][0]) == int else cluster_flat[2][0][0]
        if parent_index1 >= 0 and not person_plotted[parent_index1]:
            parent1 = flat_list[parent_index1]
        if parent_index2 >= 0 and not person_plotted[parent_index2]:
            parent2 = flat_list[parent_index2]
        if parent1 or parent2:  # add the parent nodes if valid
            person_plotted = add_child_node(tree, parent1, parent2, 
                                               flat_list[cluster_flat[0]],
                                               person_plotted, flat_list)
    # set the flag for this person
    person_parsed[cluster_flat[0]] = True
    #"""
    # plot next people
    if cluster_flat[3]:  # spouses
        for spouse in cluster_flat[3]:
            if type(spouse) == list and not person_parsed[spouse[0]]:
                plot_next_person(flat_list, tree, spouse, person_plotted, person_parsed)
    #"""
    if cluster_flat[4]:  # children
        for child in cluster_flat[4]:
            if type(child) == list and not person_parsed[child[0]]:
                plot_next_person(flat_list, tree, child, person_plotted, person_parsed)
    #"""
    if cluster_flat[1]:  # mother
        plot_next_person(flat_list, tree, cluster_flat[1][0], person_plotted, person_parsed)
    if cluster_flat[2]:  # father
        plot_next_person(flat_list, tree, cluster_flat[2][0], person_plotted, person_parsed)
    #"""
    return person_plotted


def plot_flat_master_cluster(flat_list, master_cluster_flat):
    """
    Plots a given flat master cluster using graphviz. The extra information is
    taken from the first argument, which is a flat list of all people.
    The cluster only contains indices, the flat list links the indices to 
    personal data.
    @param flat_list: Flat list containing all data for each person.
    @param master_cluster_flat: Flat cluster containing all cluster-relevant data.
    @return: Tree object containing all people from the flat list.
    """
    person_plotted = [False for _ in range(0, len(flat_list), 1)]  # helper variable
    person_parsed = [False for _ in range(0, len(flat_list), 1)]  # helper variable
    # generate basic tree with general information
    tree = graphviz.Graph(engine='dot',
                          graph_attr=graph_attributes,
                          node_attr=node_attributes,
                          edge_attr=edge_attributes,
                          encoding='utf8',
                          filename='family_tree',
                          format='png')
    # --- handle the first node ---
    person_plotted = plot_next_person(flat_list, tree, master_cluster_flat, person_plotted, person_parsed)
    # save tree to disk
    tree.save("family_tree")
    tree.view()  # show the tree
    return tree

# --- PROGRAM START ---

# step 1: get data from Excel file
family_tree_data = parse_excel_data(path)
# step 2: generate a flat list to look up data later
flat_list = generate_flat_list(family_tree_data)
# step 3: generate the master cluster with only indices
master_cluster_flat = generate_flat_master_cluster(flat_list)
# step 4: plot master cluster
tree = plot_flat_master_cluster(flat_list, master_cluster_flat)
