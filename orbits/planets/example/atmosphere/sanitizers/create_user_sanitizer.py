from nucleus.security.json_sanitizer import JsonSanitizer


class CreateUserSanitizer(JsonSanitizer):
    def sanitize(self, payload) -> dict:

        # O genérico roda primeiro: se o corpo não for objeto JSON,
        # ele recusa aqui, com o código de contrato.
        sanitized = super().sanitize(payload)

        email = sanitized.get("email")

        if isinstance(email, str):
            sanitized["email"] = email.lower()

        return sanitized
