import json
from dataclasses import dataclass


@dataclass
class Vocabulary:
    token_to_id: dict[str, int]

    pad_token = "<PAD>"
    unknown_token = "<UNK>"

    @classmethod
    def build(cls, token_sequences: list[list[str]]) -> "Vocabulary":
        token_to_id = {cls.pad_token: 0, cls.unknown_token: 1}
        for sequence in token_sequences:
            for token in sequence:
                if token not in token_to_id:
                    token_to_id[token] = len(token_to_id)
        return cls(token_to_id)

    @property
    def pad_id(self) -> int:
        return self.token_to_id[self.pad_token]

    @property
    def unknown_id(self) -> int:
        return self.token_to_id[self.unknown_token]

    def encode(self, tokens: list[str]) -> list[int]:
        return [self.token_to_id.get(token, self.unknown_id) for token in tokens]

    def encode_fixed(self, tokens: list[str], length: int) -> list[int]:
        encoded = self.encode(tokens)
        if len(encoded) > length:
            encoded = encoded[-length:]
        if len(encoded) < length:
            encoded = [self.pad_id] * (length - len(encoded)) + encoded
        return encoded

    def token_for_id(self, token_id: int) -> str:
        for token, known_id in self.token_to_id.items():
            if known_id == token_id:
                return token
        return self.unknown_token

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.token_to_id, f, indent=2, sort_keys=True)

    @classmethod
    def load(cls, path: str) -> "Vocabulary":
        with open(path, "r", encoding="utf-8") as f:
            token_to_id = json.load(f)
        return cls({str(token): int(token_id) for token, token_id in token_to_id.items()})

    def __len__(self) -> int:
        return len(self.token_to_id)
