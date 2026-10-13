#include <iostream>
#include <map>
#include <unordered_map> // For std::unordered_map
#include <algorithm>     // For std::max and std::min
#include <stdexcept>     // For std::runtime_error
#include <fstream>       // For file reading
#include <string>        // For std::string
#include <sstream>       // For std::stringstream
#include <vector>        // For std::vector
#include <climits>       // For INT_MAX
#include <iomanip>       // For std::setw

// Node class represents a single node in the tree
class Node {
public:
    long long content;        // Content of the node
    Node* left;         // Pointer to the left child
    Node* right;        // Pointer to the right child
    Node* parent;       // Pointer to the parent node
    long long height;         // Height of the node in the tree
    long long subtreeSize;    // Size of the subtree rooted at this node

    // Constructor to initialize a new node with given content
    Node(long long content) {
        this->content = content;
        this->left = NULL;
        this->right = NULL;
        this->parent = NULL;
        this->height = 1;
        this->subtreeSize = 1;
    }
};

// Tree class represents the entire AVL tree
class Tree {
public:
    Node* root;                       // Root of the tree
    std::map<long long, Node*> nodeMap;     // Map to store nodes for quick access

    // Constructor to initialize an empty tree
    Tree() {
        root = NULL;
    }

    // Insert a new node with given content into the tree
    void insert(long long content) {
        Node* newNode = new Node(content);
        nodeMap[content] = newNode;
        if (root == NULL) {
            root = newNode;
        } else {
            insertLeftMost(newNode);
        }
        updateSizeAndHeight(newNode);
        balanceTree(newNode);
    }

    // Insert a node as the leftmost node in the tree
    void insertLeftMost(Node* node) {
        Node* current = root;
        while (current->left != NULL) {
            current = current->left;
        }
        current->left = node;
        node->parent = current;
    }

    // Delete a node with the given content from the tree
    void deleteNode(long long content) {
        if (nodeMap.find(content) == nodeMap.end()) {
            throw std::runtime_error("");
        }
        Node* nodeToDelete = nodeMap[content];
        deleteNodeInternal(nodeToDelete);
        nodeMap.erase(content);
    }

    // Internal method to handle node deletion
    void deleteNodeInternal(Node* node) {
        if (node->left == NULL && node->right == NULL) {
            deleteLeafNode(node);
        } else if (node->left == NULL || node->right == NULL) {
            deleteSingleChildNode(node);
        } else {
            deleteTwoChildrenNode(node);
        }

        updateSizeAndHeight(node->parent);
        balanceTree(node->parent);
    }

    // Delete a leaf node
    void deleteLeafNode(Node* node) {
        if (node->parent == NULL) {
            root = NULL;
        } else if (node == node->parent->left) {
            node->parent->left = NULL;
        } else {
            node->parent->right = NULL;
        }
    }

    // Delete a node with a single child
    void deleteSingleChildNode(Node* node) {
        Node* child = node->left != NULL ? node->left : node->right;
        if (node->parent == NULL) {
            root = child;
            child->parent = NULL;
        } else if (node == node->parent->left) {
            node->parent->left = child;
            child->parent = node->parent;
        } else {
            node->parent->right = child;
            child->parent = node->parent;
        }
    }

    // Delete a node with two children
    void deleteTwoChildrenNode(Node* node) {
        Node* successor = findLeftmostRight(node->right);
        node->content = successor->content;
        nodeMap[node->content] = node;
        deleteNodeInternal(successor);
    }

    // Find the leftmost node in the right subtree
    Node* findLeftmostRight(Node* node) {
        while (node->left != NULL) {
            node = node->left;
        }
        return node;
    }

    // Update the size and height of nodes in the tree
    void updateSizeAndHeight(Node* node) {
        while (node != NULL) {
            node->subtreeSize = 1 + getSize(node->left) + getSize(node->right);
            node->height = 1 + std::max(getHeight(node->left), getHeight(node->right));
            node = node->parent;
        }
    }

    // Get the size of the subtree rooted at the given node
    long long getSize(Node* node) {
        if (node == NULL) {
            return 0;
        }
        return node->subtreeSize;
    }

    // Get the height of the given node
    long long getHeight(Node* node) {
        if (node == NULL) {
            return 0;
        }
        return node->height;
    }

    // Balance the tree starting from the given node
    void balanceTree(Node* node) {
        while (node != NULL) {
            long long balance = getBalance(node);
            if (balance > 1) {
                if (getBalance(node->left) < 0) {
                    node->left = rotateLeft(node->left);
                }
                node = rotateRight(node);
            } else if (balance < -1) {
                if (getBalance(node->right) > 0) {
                    node->right = rotateRight(node->right);
                }
                node = rotateLeft(node);
            }
            updateSizeAndHeight(node);
            node = node->parent;
        }
    }

    // Get the balance factor of the given node
    long long getBalance(Node* node) {
        if (node == NULL) {
            return 0;
        }
        return getHeight(node->left) - getHeight(node->right);
    }

    // Rotate the subtree left at the given node
    Node* rotateLeft(Node* node) {
        Node* newRoot = performLeftRotation(node);
        updateParentAfterRotation(node, newRoot);
        updateSizeAndHeight(node);
        updateSizeAndHeight(newRoot);
        return newRoot;
    }

    // Rotate the subtree right at the given node
    Node* rotateRight(Node* node) {
        Node* newRoot = performRightRotation(node);
        updateParentAfterRotation(node, newRoot);
        updateSizeAndHeight(node);
        updateSizeAndHeight(newRoot);
        return newRoot;
    }

    // Perform left rotation on the given node
    Node* performLeftRotation(Node* node) {
        Node* newRoot = node->right;
        node->right = newRoot->left;
        if (newRoot->left != NULL) {
            newRoot->left->parent = node;
        }
        newRoot->left = node;
        return newRoot;
    }

    // Perform right rotation on the given node
    Node* performRightRotation(Node* node) {
        Node* newRoot = node->left;
        node->left = newRoot->right;
        if (newRoot->right != NULL) {
            newRoot->right->parent = node;
        }
        newRoot->right = node;
        return newRoot;
    }

    // Update the parent pointers after a rotation
    void updateParentAfterRotation(Node* node, Node* newRoot) {
        newRoot->parent = node->parent;
        node->parent = newRoot;
        if (newRoot->parent == NULL) {
            root = newRoot;
        } else if (newRoot->parent->left == node) {
            newRoot->parent->left = newRoot;
        } else {
            newRoot->parent->right = newRoot;
        }
    }

    // Get the rank of a node with the given content
    long long getRank(long long content) {
        if (nodeMap.find(content) == nodeMap.end()) {
            throw std::runtime_error("");
        }
        Node* node = nodeMap[content];
        long long rank = 0;
        if (node->left != NULL) {
            rank += getSize(node->left);
        }

        // Traverse up the tree to calculate the rank
        while (node->parent != NULL) {
            if (node == node->parent->right) {
                rank += getSize(node->parent) - getSize(node);
                node = node->parent;
            } else {
                node = node->parent;
            }
        }
        return rank;
    }
};


// Function to initialize reuse distances with predefined thresholds
std::map<std::string, long long> initReuseDistances() {
    // Initialize map with specific keys and default values
    std::map<std::string, long long> reuseDistances = {
        {"avg", 0},
        {"min", std::numeric_limits<long long>::max()},
        {"max", -1},
        {"0", 0},
        {">512K", 0}
    };
    
    // Add keys for reuse distances up to 256K with doubling steps
    for (long long i = 1; i < 512 * 1024; i *= 2) {
        if (i < 1024) {
            reuseDistances[std::to_string(i)] = 0;
        } else {
            long long temp = i / 1024;
            reuseDistances[std::to_string(temp) + "K"] = 0;
        }
    }

    return reuseDistances;
}

// Function to update reuse distance statistics
void updateReuseDistance(long long rank, std::map<std::string, long long>& reuseDistances) {
    reuseDistances["avg"] += rank;
    reuseDistances["min"] = std::min(reuseDistances["min"], rank);
    reuseDistances["max"] = std::max(reuseDistances["max"], rank);

    // Handle ranks greater than 128K separately
    if (rank > 512 * 1024) {
        reuseDistances[">512K"] += 1;
        return;
    }

    // Define thresholds for reuse distances
    std::vector<std::pair<long long, std::string>> thresholds = {
        {0, "0"},
        {1, "1"},
        {2, "2"},
        {4, "4"},
        {8, "8"},
        {16, "16"},
        {32, "32"},
        {64, "64"},
        {128, "128"},
        {256, "256"},
        {512, "512"},
        {1024, "1.0K"},
        {2048, "2.0K"},
        {4096, "4.0K"},
        {8192, "8.0K"},
        {16384, "16.0K"},
        {32768, "32.0K"},
        {65536, "64.0K"},
        {131072, "128.0K"},
        {262144, "256.0K"},
        {524388, "512.0K"}
    };

    // Update the corresponding threshold in the map
    for (const auto& threshold : thresholds) {
        if (rank < threshold.first) {
            reuseDistances[threshold.second] += 1;
            return;
        }
    }
}

// Function to calculate reuse distances from a trace file
std::map<std::string, long long> computeReuseDistances(const std::string& traceFileName) {
    Tree tree;  // Tree to store and manage ranks
    std::unordered_map<std::string, long long> lastOccurrence;  // Map to store last occurrences
    std::map<std::string, long long> reuseDistances = initReuseDistances();  // Initialize reuse distances
    long long reuseCount = 0;  // Counter for no reuse data

    std::ifstream traceFile(traceFileName);
    std::string line;
    long long index = 0;

    // Read each line from the trace file
    while (std::getline(traceFile, line)) {
        std::istringstream ss(line);
        std::string offset, dummy;
        std::getline(ss, dummy, ',');
        std::getline(ss, dummy, ',');
        std::getline(ss, offset, ',');

        // If the offset was seen before, calculate reuse distance
        if (lastOccurrence.find(offset) != lastOccurrence.end()) {
            reuseCount++;
            long long lastIndex = lastOccurrence[offset];
            long long rank = tree.getRank(lastIndex);
            updateReuseDistance(rank, reuseDistances);
            tree.deleteNode(lastIndex);
        }

        // Update the last occurrence and insert the current index into the tree
        lastOccurrence[offset] = index;
        tree.insert(index);
        index++;
    }

    // Calculate the average reuse distance
    if (reuseCount > 0) {
        reuseDistances["avg"] /= reuseCount;
    }

    return reuseDistances;
}

// Main function to process multiple input files
int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <input_file1> <input_file2> ... <input_fileN>" << std::endl;
        return 1;
    }

    // Define keys for reuse distances
    std::vector<std::string> keys = {
        "avg", "min", "max", "0", "1", "2", "4", "8", "16", "32", "64", "128", "256", "512", "1.0K",
        "2.0K", "4.0K", "8.0K", "16.0K", "32.0K", "64.0K", "128.0K", "256.0K", "512.0K", ">512K"
    };

    // Print the header for the output table
    std::cout << std::setw(10) << "File";
    for (const auto& key : keys) {
        std::cout << std::setw(10) << key;
    }
    std::cout << std::endl;

    // Process each input file and calculate reuse distances
    for (int i = 1; i < argc; ++i) {
        std::string traceFileName = argv[i];
        std::map<std::string, long long> reuseDistances = computeReuseDistances(traceFileName);
        std::cout << std::setw(10) << traceFileName;
        for (const auto& key : keys) {
            if (reuseDistances.find(key) != reuseDistances.end()) {
                std::cout << std::setw(10) << reuseDistances.at(key);
            }
        }
        std::cout << std::endl;
    }

    return 0;
}