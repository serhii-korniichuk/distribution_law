import re


class Token:
    def __init__(self, category_, content, position=None):
        self.category = category_
        self.content = content
        self.position = position

    def __repr__(self):
        return f"Token(category={self.category}, data={self.content})"


class Tree:
    def __init__(self, data):
        self.data = data
        self.left_child = None
        self.right_child = None


class Expression:
    def __init__(self, input_expr):
        self.input_expr = input_expr
        self.token_list = []
        self.error_list = []

    def tokenize(self):
        pattern = r'(\d*\.?\d+|\+|\-|\*|\/|\(|\)|[a-zA-Z]+)'
        matches = re.findall(pattern, self.input_expr)

        for match in matches:
            if match[0].isdigit() or match[0] == '.':
                self.token_list.append(Token("NUMBER", match))
            elif match.isalpha():
                self.token_list.append(Token("VARIABLE", match))
            else:
                self.token_list.append(Token("OPERATOR", match))


def locate_matching_bracket(tokens, start_idx, search_direction):
    balance = 0
    step = 1 if search_direction == "forward" else -1

    for idx in range(start_idx, len(tokens) if search_direction == "forward" else -1, step):
        if tokens[idx].content == "(":
            balance += 1
        elif tokens[idx].content == ")":
            balance -= 1
        if balance == 0:
            return idx

    return -1


def refine_tokens(token_sequence):
   changes_made = True

   while changes_made:
       changes_made = False
       buffer = []

       for idx in range(len(token_sequence)):
           current = token_sequence[idx]
           previous = buffer[-1] if buffer else None

           if current.content == "-" and (previous is None or previous.content == "("):
               buffer.append(Token("NUMBER", "0"))
               buffer.append(current)
               changes_made = True
           elif current.content == "0" and previous and previous.content == "/":
               raise ZeroDivisionError("Attempted division by zero")
           elif current.content == "1" and previous and previous.content in ("*", "/"):
               buffer.pop()
               changes_made = True
           elif current.content == "0" and previous and previous.content in ("+", "-"):
               buffer.pop()
               changes_made = True
           else:
               buffer.append(current)

       token_sequence = buffer

   return token_sequence


def convert_infix_to_postfix(tokens):
    precedence = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    output_queue = []
    operator_stack = []

    for token in tokens:
        if token.category in ("NUMBER", "VARIABLE"):
            output_queue.append(token)
        elif token.content in precedence:
            while operator_stack and operator_stack[-1].content != "(" and precedence.get(operator_stack[-1].content, 0) >= precedence[token.content]:
                output_queue.append(operator_stack.pop())
            operator_stack.append(token)
        elif token.content == "(":
            operator_stack.append(token)
        elif token.content == ")":
            while operator_stack and operator_stack[-1].content != "(":
                output_queue.append(operator_stack.pop())
            if operator_stack:
                operator_stack.pop()

    while operator_stack:
        if operator_stack[-1].content == "(":
            raise ZeroDivisionError("Mismatched parentheses")
        output_queue.append(operator_stack.pop())

    return output_queue


def construct_expression_tree(postfix_tokens):
   stack = []
   for token in postfix_tokens:
       if token.category in ("NUMBER", "VARIABLE"):
           stack.append(Tree(token.content))
       else:
           node = Tree(token.content)
           if len(stack) < 2:
               raise ZeroDivisionError("Invalid expression")
           node.right_child = stack.pop()
           node.left_child = stack.pop()
           stack.append(node)
   if not stack:
       raise ZeroDivisionError("Empty expression")
   return stack[0]


def tree_to_infix(tree):
   if tree is None:
       return ""

   if tree.data in ['+', '-', '*', '/']:
       left_child = tree_to_infix(tree.left_child)
       right_child = tree_to_infix(tree.right_child)

       if tree.data in ['+', '-']:
           if right_child and tree.right_child.data in ['*', '/', '+', '-']:
               right_child = f"({right_child})"
           if tree.left_child and tree.left_child.data in ['*', '/', '+', '-']:
               left_child = f"({left_child})"
       elif tree.data in ['*', '/']:
           if tree.right_child and tree.right_child.data in ['+', '-']:
               right_child = f"({right_child})"
           if tree.left_child and tree.left_child.data in ['+', '-']:
               left_child = f"({left_child})"

       return f"{left_child}{tree.data}{right_child}"
   else:
       return tree.data


def visualize_tree(tree, level=0):
    if tree:
        visualize_tree(tree.right_child, level + 1)
        print('  ' * level + str(tree.data))
        visualize_tree(tree.left_child, level + 1)


def apply_distributive_law(node, level=0):
   if node is None:
       return None, False

   changed = False

   if node.data == '*':
       if node.right_child and node.right_child.data in ['+', '-']:
           node = distribute_multiplication(node.left_child, node.right_child)
           changed = True
       elif node.left_child and node.left_child.data in ['+', '-']:
           node = distribute_multiplication(node.right_child, node.left_child)
           changed = True

   if changed:
       node.left_child, left_changed = apply_distributive_law(node.left_child, level + 1)
       node.right_child, right_changed = apply_distributive_law(node.right_child, level + 1)
       changed = changed or left_changed or right_changed
   else:
       new_left, left_changed = apply_distributive_law(node.left_child, level + 1)
       new_right, right_changed = apply_distributive_law(node.right_child, level + 1)
       node.left_child = new_left
       node.right_child = new_right
       changed = left_changed or right_changed

   return node, changed


def distribute_multiplication(factor, sum_node):
    new_node = Tree(sum_node.data)

    left_mult = Tree('*')
    left_mult.left_child = copy_node(factor)
    left_mult.right_child = copy_node(sum_node.left_child)

    right_mult = Tree('*')
    right_mult.left_child = copy_node(factor)
    right_mult.right_child = copy_node(sum_node.right_child)

    new_node.left_child = left_mult
    new_node.right_child = right_mult

    return new_node


def copy_node(node):
    if node is None:
        return None

    new_node = Tree(node.data)

    new_node.left_child = copy_node(node.left_child)
    new_node.right_child = copy_node(node.right_child)

    return new_node


def test_expression_step_by_step(test_expr):
    expr = Expression(test_expr)
    expr.tokenize()
    optimized_tokens = refine_tokens(expr.token_list)
    postfix_tokens = convert_infix_to_postfix(optimized_tokens)
    tree = construct_expression_tree(postfix_tokens)

    print("\nInitial expression:")
    print(tree_to_infix(tree))

    print("\nInitial tree of expression:")
    visualize_tree(tree)

    iteration = 1

    while True:
        tree, changed = apply_distributive_law(tree)
        if changed:
            print(f"\nIteration {iteration}:")
            print(tree_to_infix(tree))
            print(f"\nTree iteration {iteration}:")
            visualize_tree(tree)
            iteration += 1
        else:
            break

    return tree

expressions = [
    "(a + b) * c",
    "(a + b - 2) * c",
    "(a - b + 3) * (c - d)",
    "(a - b) * c - (d + e) * (d * 1.5 - g) / (f + g)"
]

for expression in expressions:
    final_tree = test_expression_step_by_step(expression)
    print("\nResult:")
    print(tree_to_infix(final_tree))