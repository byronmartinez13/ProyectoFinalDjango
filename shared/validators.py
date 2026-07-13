import re

from django.core.exceptions import ValidationError

_LETTERS_RE = re.compile(r'^[A-Za-zÀ-ÖØ-öø-ÿÑñ]+(?:[ \'-][A-Za-zÀ-ÖØ-öø-ÿÑñ]+)*$')


def validate_only_letters(value):
    """Valida que el valor contenga solo letras (incluye tildes y Ñ),
    con espacios simples o guiones entre palabras (ej. "José Luis",
    "Pérez-Vera"). Se usa en nombres y apellidos de clientes/usuarios."""
    if not _LETTERS_RE.match((value or '').strip()):
        raise ValidationError(
            'Este campo solo debe contener letras (sin números ni símbolos).',
            code='invalid_letters',
        )


def validate_phone_ec(value):
    """Valida un teléfono ecuatoriano: convencional (7-9 dígitos), celular
    (10 dígitos, inicia en 0) o formato internacional +593 seguido de 9
    dígitos."""
    cleaned = (value or '').strip().replace(' ', '').replace('-', '')

    if cleaned.startswith('+593'):
        digits = cleaned[4:]
        valid = digits.isdigit() and len(digits) == 9
    else:
        valid = cleaned.isdigit() and 7 <= len(cleaned) <= 10

    if not valid:
        raise ValidationError(
            'Ingresa un teléfono válido: 7 a 10 dígitos (ej. 0991234567) '
            'o +593 seguido de 9 dígitos.',
            code='invalid_phone',
        )


def validate_cedula_ec(value):
    """
    Valida cédula ecuatoriana (10 dígitos) o RUC (13 dígitos)
    usando el algoritmo oficial del Registro Civil de Ecuador.
    
    Algoritmo:
    1. La cédula tiene 10 dígitos
    2. Los 2 primeros dígitos son el código de provincia (01-24)
    3. El tercer dígito debe ser menor a 6
    4. Se multiplican los dígitos alternadamente por 2 y 1
    5. Si el resultado > 9, se resta 9
    6. Se suman todos los resultados
    7. El dígito verificador = (decena superior - suma) mod 10
    
    Uso en modelo:
        from shared.validators import validate_cedula_ec
        dni = CharField(validators=[validate_cedula_ec])
    
    Ejemplo:
        validate_cedula_ec("0912345678")  # Válida o lanza error
    """

    # --- Paso 1: Verificar que solo contenga números ---
    if not value.isdigit():
        raise ValidationError(
            'El ID solo debe contener números.',
            code='invalid_chars'
        )

    # --- Paso 2: Verificar longitud ---
    # Cédula = 10 dígitos, RUC = 13 dígitos
    if len(value) not in (10, 13):
        raise ValidationError(
            'El ID debe tener 10 dígitos (cédula) o 13 dígitos (RUC).',
            code='invalid_length'
        )

    # --- Paso 3: Verificar código de provincia ---
    # Los 2 primeros dígitos = provincia (01 a 24)
    province = int(value[:2])
    if province < 1 or province > 24:
        raise ValidationError(
            f'Código provincial inválido: {province}. Debe estar entre 01 y 24.',
            code='invalid_province'
        )

    # --- Paso 4: Verificar tercer dígito ---
    third_digit = int(value[2])
    if third_digit >= 6:
        raise ValidationError(
            'El tercer dígito debe ser menos que 6 para personas naturales.',
            code='invalid_third'
        )

    # --- Paso 5: Algoritmo de validación (Módulo 10) ---
    coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]  # Coeficientes
    total = 0

    for i in range(9):
        result = int(value[i]) * coefficients[i]
        # Si el resultado es mayor a 9, restar 9
        if result > 9:
            result -= 9
        total += result

    # --- Paso 6: Calcular dígito verificador ---
    # Decena superior - total
    verifier = 10 - (total % 10)
    if verifier == 10:
        verifier = 0

    # --- Paso 7: Comparar con el décimo dígito ---
    if verifier != int(value[9]):
        raise ValidationError(
            'Número ID inválido. El número de ID ingresado es incorrecto.',
            code='invalid_verifier'
        )

    # Si llegamos aquí, la cédula es válida
    return value
