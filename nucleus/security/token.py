"""
Emissão e verificação de token JWT.

O token substitui a sessão guardada no servidor: ele carrega a
identidade (`sub`) e a validade (`exp`), assinado com a SECRET_KEY
da aplicação. Se alguém alterar o conteúdo, a assinatura deixa de
bater e a verificação recusa (SOLAR-ARCH-027).
"""

import jwt

from datetime import datetime, timedelta, timezone


class Token:

    def __init__(self, secret_key: str, expires_hours: int):
        self.secret_key = secret_key
        self.expires_hours = expires_hours

    def create(self, id_user: int) -> str:
        """
        Emite um token para o usuário.
        """

        expire_time = timedelta(hours=self.expires_hours)

        payload = {
            # `sub` é padronizado, e vai como STRING: o JWT não
            # aceita número nesta chave.
            "sub": str(id_user),

            # `exp` é o prazo. Um token vazado deixa de servir
            # sozinho quando o prazo passa — é o que limita a janela
            # de uso de um token roubado.
            "exp": datetime.now(timezone.utc) + expire_time
        }

        # Algoritmo EXPLÍCITO (SOLAR-ARCH-027). Um `encode` sem
        # algoritmo declarado pode cair em token sem assinatura
        # nenhuma.
        return jwt.encode(
            payload,
            self.secret_key,
            algorithm="HS256"
        )

    def verify(self, token: str) -> dict:
        """
        Confere o token e devolve o conteúdo.
        """

        if not token:
            raise ValueError("Token não fornecido")

        # Aceita o formato do cabeçalho HTTP ("Bearer <token>") e o
        # token puro — quem chama não precisa decidir qual dos dois
        # chegou.
        if token.startswith("Bearer "):
            token = token[7:]

        try:
            # `algorithms` EXPLÍCITO na verificação.
            #
            # Sem a lista, a biblioteca aceitaria o algoritmo
            # declarado NO PRÓPRIO token — e bastaria dizer
            # `alg: none` para entrar sem assinatura
            # (SOLAR-ARCH-027).
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"]
            )

        # Expirado e inválido viram mensagens DIFERENTES de
        # propósito: quem está com a tela aberta precisa saber que é
        # só entrar de novo, e não que a sessão foi corrompida.
        except jwt.ExpiredSignatureError:
            raise ValueError(
                "Sessão expirada. Faça login novamente"
            )

        except jwt.InvalidTokenError:
            raise ValueError(
                "Token inválido"
            )