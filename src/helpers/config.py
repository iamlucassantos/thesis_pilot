"""Module that define configuration of algorithms."""
from pydantic import BaseModel, validator
import numpy as np
from typing import Optional


class ConfigLinearAircraft(BaseModel):
    """Symmetric derivatives."""
    policy_type: str = "MlpPolicy"
    env_name: Optional[str] = "citation"
    filename: Optional[str] = "citation.yaml"
    configuration: Optional[str] = "symmetric"
    algorithm: Optional[str] = ""
    seed: Optional[int] = None  # Random seed
    dt: Optional[float] = 0.1  # Time step
    episode_steps: Optional[int] = 100  # Number of steps
    learning_steps: Optional[int] = 1000  # Number of total learning steps
    task: Optional[str] = "aoa"
    run: int = 0  # Number of times to run the environment after learning
    reward_scale: float = 1.0  # Reward scale
    log_interval: int = 1  # Log interval
    reward_type: str = "sq_error"

    @validator('configuration')
    def check_config(cls, configuration):
        CONFIGURATIONS = ['symmetric', 'sp', 'asymmetric']  # Available aircraft configurations
        if configuration not in CONFIGURATIONS:
            raise ValueError(f"Configuration must be in {CONFIGURATIONS}")

        return configuration

    @validator('task')
    def check_task(cls, task):
        TASKS = ['aoa', 'aoa_sin', 'q', 'q_sin']  # Available tasks
        if task not in TASKS:
            raise ValueError(f"Task must be in {TASKS}")
        return task

    @validator('seed')
    def check_seed(cls, seed):
        if seed is None:
            seed = np.random.randint(1_000)
        return seed
