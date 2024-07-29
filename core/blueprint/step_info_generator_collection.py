from typing import Dict, Type, Iterator
from collections.abc import Iterable

from ._step_abstract import StepInfoGenerator

class StepInfoGeneratorCollection:
    def __init__(self):
        self._generators: Dict[str, StepInfoGenerator] = {}

    def add(self, generator: StepInfoGenerator) -> None:
        # Get the step_model class from the generator
        step_model_class = generator.step_model

        # Instantiate the step_model class
        step_model_instance = step_model_class()

        # Get the type attribute from the instance
        type_key = step_model_instance.type

        # Add the generator to the dictionary with the type as the key
        self._generators[type_key] = generator

    def __iter__(self) -> Iterator[tuple[str, StepInfoGenerator]]:
        return iter(self._generators.items())

    def __getitem__(self, key: str) -> StepInfoGenerator:
        return self._generators[key]

    def __len__(self) -> int:
        return len(self._generators)

    def items(self) -> Iterable[tuple[str, StepInfoGenerator]]:
        return self._generators.items()

    def keys(self) -> Iterable[str]:
        return self._generators.keys()

    def values(self) -> Iterable[StepInfoGenerator]:
        return self._generators.values()