from datetime import datetime, timezone
from typing import Any

class CreateUserOutput:


    def to_object(data) -> dict:

        created_at = data.user.data_created_user

        # Em bancos que devolvem o default só depois do INSERT, o
        # atributo pode chegar vazio; o contrato de dados não pode.
        if not isinstance(created_at, datetime):
            created_at = datetime.now(timezone.utc)
        
        return {
            "id": data.id_user,
            "name": data.name_user,
            "email": data.email_user,
            "created_at": data.created_at_user.isoformat(),
        }
    