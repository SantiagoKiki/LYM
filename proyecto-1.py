import re

class RobotParser:
    def __init__(self, program):
        self.program = program
        self.tokens = self.tokenize(program)
        self.current_token_index = 0
        self.variables = {}
        self.macros = {}
        self.commands = {
            "turnToMy", "turnToThe", "walk", "jump", "drop", "pick", 
            "grab", "letgo", "pop", "moves", "nop", "safeExe", "if", "else", "fi", "then","foo", "move","goend","repeat","times","while","not","roomForChips"    
        }
        self.constants = {
            "size", "myX", "myY", "myChips", "myBalloons", 
            "balloonsHere", "chipsHere", "roomForChips",
        }
        self.conditions = {
            "isBlocked?", "isFacing?", "zero?", "not?"
        }
        self.directions = {"left", "right", "back", "forward"}
        self.orientations = {"north", "south", "east", "west"}
        self.block_balance = 0  # Para rastrear el equilibrio de los bloques

    def tokenize(self, program):
        token_specification = [
            ("NUMBER", r"\d+"),
            ("ID", r"[A-Za-z_]\w*\??"),  # Incluir ? como parte de ID en condiciones
            ("ASSIGN", r"="),
            ("OP", r"[\+\-\*/]"),
            ("SEMICOLON", r";"),
            ("LPAREN", r"\("),
            ("RPAREN", r"\)"),
            ("LBRACE", r"\{"),
            ("RBRACE", r"\}"),
            ("COMMA", r","),
            ("NEWLINE", r"\n"),
            ("SKIP", r"[ \t]+"),  # Ignorar espacios y tabuladores
            ("MISMATCH", r"."),  # Cualquier otro carácter no reconocido
        ]
        token_regex = "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in token_specification)

        tokens = []
        for mo in re.finditer(token_regex, program):
            kind = mo.lastgroup
            value = mo.group(kind)
            if kind in ["NEWLINE", "SKIP"]:
                continue  # Saltar estos tokens
            elif kind == "MISMATCH":
                raise RuntimeError(f"Carácter inesperado: {value}")
            tokens.append((kind, value))

        print(f"Tokens generados: {tokens}")  # Depuración para ver todos los tokens
        return tokens

    def parse(self):
        try:
            while self.current_token_index < len(self.tokens):
                print(f"Parseando instrucción en índice {self.current_token_index}: {self.tokens[self.current_token_index]}")
                self.parse_instruction()

            # Verificar si todos los bloques y paréntesis han sido cerrados
            if self.block_balance != 0:
                raise RuntimeError("Desequilibrio de bloques: faltan corchetes de cierre")

            print("El programa es correcto.")
        except RuntimeError as e:
            print(f"Error encontrado: {e}")
            print("El programa es incorrecto.")

    def parse_instruction(self):
        token = self.tokens[self.current_token_index]
        print(f"Procesando token: {token}")
    
        if token[0] == "ID" and token[1] == "NEW":
            print("Encontrado NEW")
            self.current_token_index += 1  # Saltar "NEW"
            self.parse_new()  # Procesar la instrucción NEW (VAR o MACRO)
        elif token[0] == "ID" and token[1] == "EXEC":
            self.parse_exec()
        elif token[0] == "ID" and token[1] == "if":
            self.parse_if()
        elif token[0] == "ID" and token[1] == "else":
            self.parse_else()
        elif token[0] == "ID" and token[1] == "fi":
            print("Fin del bloque if")
            self.current_token_index += 1  # Saltar "fi"
        elif token[0] == "ID":
            self.parse_command()  # Para cualquier comando que no sea estructural
        elif token[0] == "LBRACE":
            self.block_balance += 1  # Incrementar el balance de bloques
            self.current_token_index += 1
            print(f"Bloque abierto. Balance actual: {self.block_balance}")
        elif token[0] == "RBRACE":
            self.block_balance -= 1  # Decrementar el balance de bloques
            print(f"Bloque cerrado. Balance actual: {self.block_balance}")
            if self.block_balance < 0:
                raise RuntimeError('Se encontró un "}" sin un "{" correspondiente')
            self.current_token_index += 1
        elif token[0] == "LPAREN":
            self.parse_parentheses()  # Verificar el contenido dentro de paréntesis
        elif token[0] == "SEMICOLON":
            print("Encontrado punto y coma, saltando")
            self.current_token_index += 1  # Saltar el punto y coma
        else:
            raise RuntimeError(f"Instrucción no reconocida: {token}")

    def parse_new(self):
        token = self.tokens[self.current_token_index]
        print(f"Procesando NEW con token: {token}")
        if token[0] == "ID" and token[1] == "VAR":
            self.parse_variable_declaration()
        elif token[0] == "ID" and token[1] == "MACRO":
            self.parse_macro_declaration()
        else:
            raise RuntimeError("Se esperaba 'VAR' o 'MACRO' después de 'NEW'")

    def parse_variable_declaration(self):
        print("Procesando declaración de variable")
        self.current_token_index += 1  # Saltar "VAR"
        var_name = self.tokens[self.current_token_index][1]
        print(f"Variable: {var_name}")
        self.current_token_index += 1  # Avanzar al nombre de la variable

        if self.tokens[self.current_token_index][0] == "ASSIGN":
            self.current_token_index += 1  # Saltar "="
            var_value = self.tokens[self.current_token_index][1]
            print(f"Asignando valor: {var_value}")
            self.current_token_index += 1  # Avanzar al valor de la variable

            self.variables[var_name] = var_value
            print(f"Variable declarada: {var_name} = {var_value}")
        else:
            raise RuntimeError("Se esperaba un operador de asignación después de 'VAR'")

    def parse_macro_declaration(self):
        print("Procesando declaración de macro")
        self.current_token_index += 1  # Saltar "MACRO"
        
        if self.current_token_index >= len(self.tokens):
            raise RuntimeError('Unexpected end of input while parsing macro declaration')
        
        macro_name = self.tokens[self.current_token_index][1]
        print(f"Macro: {macro_name}")
        self.current_token_index += 1  # Avanzar al nombre del macro

        if self.tokens[self.current_token_index][0] == "LPAREN":
            print("Procesando parámetros del macro")
            self.current_token_index += 1  # Saltar "("
            parameters = []
            while self.tokens[self.current_token_index][0] != "RPAREN":
                parameters.append(self.tokens[self.current_token_index][1])
                self.current_token_index += 1
                if self.tokens[self.current_token_index][0] == "COMMA":
                    self.current_token_index += 1  # Saltar comas entre parámetros
            self.current_token_index += 1  # Saltar ")"
            print(f"Parámetros: {parameters}")

        if self.tokens[self.current_token_index][0] == "LBRACE":
            self.block_balance += 1  # Incrementar el balance por el bloque abierto
            self.current_token_index += 1  # Saltar "{"
            while self.tokens[self.current_token_index][0] != "RBRACE":
                if self.current_token_index >= len(self.tokens):
                    raise RuntimeError('Se esperaba "}" para cerrar el bloque del macro')
                self.parse_instruction()  # Procesar el contenido del bloque de la macro
            self.block_balance -= 1  # Decrementar el balance por el bloque cerrado
            self.current_token_index += 1  # Saltar "}"
            print(f"Bloque del macro cerrado, balance actual: {self.block_balance}")
        else:
            raise RuntimeError('Se esperaba "{" después de los parámetros del macro')

    def parse_if(self):
        print("Procesando if")
        self.current_token_index += 1  # Saltar "if"
        condition = self.parse_expression()
        print(f"Condición: {condition}")

        # Procesar el bloque if
        if self.tokens[self.current_token_index][0] == "LBRACE":
            self.parse_block()
        if self.tokens[self.current_token_index][0] == "then":
            self.current_token_index += 1  # Saltar "then"
            if self.tokens[self.current_token_index][0] == "LBRACE":
                self.block_balance += 1  # Incrementar el balance de bloques
                self.parse_block()  # Procesar el bloque de código después de then

        # Procesar el else si existe
        if self.tokens[self.current_token_index][0] == "else":
            self.parse_else()

            # Verificar y avanzar el "fi"
            if self.tokens[self.current_token_index][0] == "fi":
                print("Encontrado fi")
                self.current_token_index += 1  # Saltar "fi"
            else:
                raise RuntimeError('Se esperaba "fi" al final de la estructura if-else')

    def parse_else(self):
        print("Procesando else")
        self.current_token_index += 1  # Saltar "else"
        if self.tokens[self.current_token_index][0] == "LBRACE":
            self.parse_block()
        else:
            raise RuntimeError('Se esperaba "{" después de "else"')

    def parse_block(self):
        print("Procesando bloque")
        if self.tokens[self.current_token_index][0] == "LBRACE":
            self.block_balance += 1  # Incrementar el balance por el bloque abierto
            self.current_token_index += 1  # Saltar '{'
            while self.tokens[self.current_token_index][0] != "RBRACE" or self.block_balance > 1:
                if self.current_token_index >= len(self.tokens):
                    raise RuntimeError('Se esperaba "}" para cerrar el bloque')
                self.parse_instruction()
            self.block_balance -= 1  # Decrementar el balance por el bloque cerrado
            print(f"Bloque cerrado. Balance actual: {self.block_balance}")
            self.current_token_index += 1  # Saltar '}'
        else:
            raise RuntimeError('Se esperaba "{" para iniciar un bloque')

    def parse_command(self):
        command = self.tokens[self.current_token_index][1]
        print(f"Procesando comando: {command}")

        if command in self.commands or command in self.macros:
            self.current_token_index += 1

            if self.current_token_index < len(self.tokens) and self.tokens[self.current_token_index][0] == "LPAREN":
                self.parse_parentheses()  # Procesar paréntesis si existen

            # Ejecutar un macro si existe
            if command in self.macros:
                print(f"Ejecutando macro: {command}")
                self.execute_macro(command)

        elif command in self.constants:
            print(f"Constante encontrada: {command}")
            self.current_token_index += 1

        elif command in self.conditions:
            print(f"Condición encontrada: {command}")
            self.current_token_index += 1

        elif command in self.directions:
            print(f"Dirección encontrada: {command}")
            self.current_token_index += 1

        elif command in self.orientations:
            print(f"Orientación encontrada: {command}")
            self.current_token_index += 1

        elif command in self.variables:
            print(f"Variable usada: {command}")
            self.current_token_index += 1

        else:
            raise RuntimeError(f"Comando o token no reconocido: {command}")


    def parse_expression(self):
        token = self.tokens[self.current_token_index]
        print(f"Procesando expresión: {token}")

        if token[0] == "ID":
            next_token_index = self.current_token_index + 1
            if next_token_index < len(self.tokens):
                next_token = self.tokens[next_token_index]
                # Simplemente devuelve el token con la condición completa (ya contiene ? si aplica)
                self.current_token_index += 1
                return token[1]
            else:
                # Si no hay más tokens, solo devolvemos el token actual
                self.current_token_index += 1
                return token[1]
        else:
            raise RuntimeError(f"Expresión no reconocida: {token}")


    def parse_parentheses(self):
        print("Procesando paréntesis")
        balance = 1
        self.current_token_index += 1  # Saltar '('
        while balance > 0:
            if self.tokens[self.current_token_index][0] == "LPAREN":
                balance += 1
            elif self.tokens[self.current_token_index][0] == "RPAREN":
                balance -= 1
            if self.current_token_index >= len(self.tokens):
                raise RuntimeError('Se esperaba ")" para cerrar el paréntesis')
            self.current_token_index += 1
        print("Paréntesis balanceado")

    def parse_exec(self):
        print("Procesando EXEC")
        self.current_token_index += 1
        if self.tokens[self.current_token_index][0] == "LBRACE":
            self.block_balance += 1  # Incrementar el balance por el bloque abierto
            self.current_token_index += 1
            exec_body = []
            while self.tokens[self.current_token_index][0] != "RBRACE":
                if self.current_token_index >= len(self.tokens):
                    raise RuntimeError('Se esperaba "}" para cerrar el bloque de EXEC')
                self.parse_instruction()  # Procesar el contenido del bloque EXEC
            self.block_balance -= 1  # Decrementar el balance por el bloque cerrado
            self.current_token_index += 1  # Saltar '}'
            print(f"Bloque EXEC cerrado, balance actual: {self.block_balance}")
        else:
            raise RuntimeError('Se esperaba "{" después de EXEC')

    def execute_macro(self, macro_name):
        parameters, macro_body = self.macros[macro_name]
        print(f"Ejecutando macro: {macro_name} con cuerpo {macro_body}")
        
        if self.tokens[self.current_token_index][0] == "LBRACE":
            self.block_balance += 1  # Incrementar el balance por el bloque abierto
            self.current_token_index += 1
            while self.tokens[self.current_token_index][0] != "RBRACE":
                if self.current_token_index >= len(self.tokens):
                    raise RuntimeError('Se esperaba "}" para cerrar el bloque del macro')
                self.parse_instruction()  # Procesar el contenido del bloque de la macro
            self.block_balance -= 1  # Decrementar el balance por el bloque cerrado
            self.current_token_index += 1  # Saltar '}'
            print(f"Bloque del macro cerrado, balance actual: {self.block_balance}")
        else:
            raise RuntimeError('Se esperaba "{" después de los parámetros del macro')

# Leer el contenido del archivo
with open("code-examples.txt", "r") as file:
    program = file.read()

parser = RobotParser(program)
parser.parse()
