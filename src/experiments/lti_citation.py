"""Experiment to learn using wandb while using the citation model."""

import matplotlib.pyplot as plt
from stable_baselines3 import SAC
from wandb.integration.sb3 import WandbCallback
from stable_baselines3.common.monitor import Monitor
from rich.pretty import pprint

import wandb
from helpers.paths import Path
from models.aircraft_environment import AircraftEnv
from helpers.config import ConfigLinearAircraft
import pathlib as pl


def main(algorithm_name: str = "SAC", env_name: str = "citation",
         task="aoa", seed: int = 1, dt: float = 0.1,
         episode_steps: int = 500, learning_steps: int = 100_000,
         TO_TRAIN: bool = True, TO_PLOT: bool = False, verbose: int =1):
    """Main function to run the experiment.

    args:
        algorithm_name: Name of the algorithm used.
        env_name: Environment to use.

    """

    config = ConfigLinearAircraft(
        algorithm=algorithm_name,
        env_name=env_name,
        seed=seed,
        dt=dt,
        episode_steps=episode_steps,
        learning_steps=learning_steps,
        task=task,
    )

    if verbose > 0:
        pprint(config.asdict)

    # Get environment
    if env_name == "citation":
        env = AircraftEnv(config)
    else:
        raise ValueError(f"Environment {env_name} not implemented.")

    # Define project name and paths
    project_name = f"{config.env_name}-{config.algorithm} v2"
    MODELS_PATH = Path.models / project_name
    LOGS_PATH = Path.logs / project_name

    if TO_TRAIN:

        # Start wandb
        run = wandb.init(
            project=project_name,
            config=config.asdict,
            sync_tensorboard=True,  # auto-upload sb3's tensorboard metrics
            save_code=True,  # optional
        )

        # Create directories
        pl.Path.mkdir(MODELS_PATH / run.name, parents=True, exist_ok=True)
        pl.Path.mkdir(LOGS_PATH, parents=True, exist_ok=True)

        # Wrap environment with monitor
        env = Monitor(env, filename=f"{MODELS_PATH}/{run.name}")

        # Load wandb callback
        wandb_callback = WandbCallback(
            model_save_freq=100,
            # gradient_save_freq=config.episode_steps,
            model_save_path=f"{MODELS_PATH / run.name}",
            verbose=2)

        # Creates the model algorithm

        if config.algorithm == "SAC":
            algo = SAC
        else:
            raise ValueError(f"Algorithm {config.algorithm} not implemented.")

        # Create model
        model = algo("MlpPolicy", env, verbose=2,
                     tensorboard_log=LOGS_PATH)

        # Learn model
        model.learn(total_timesteps=config.learning_steps,
                    callback=[wandb_callback],
                    log_interval=2,
                    tb_log_name=run.name,
                    progress_bar=True)

        # Replace previous latest-model with the new model
        model.save(f"{MODELS_PATH}/latest-model")

    else:
        model_name = "olive-sun-4"
        model = SAC.load(Path.models / project_name / model_name / "model.zip")

    for _ in range(1):
        obs = env.reset()

        for i in range(config.episode_steps):
            action, _states = model.predict(obs, deterministic=True)

            obs, reward, done, info = env.step(action)
            env.render()

            if wandb.run is not None:
                wandb.log({f"reward": reward})
                wandb.log({f"reference": env.reference[-1]})
                wandb.log({f"state": env.track[-1]})

            if done:
                print(f"finished at {i}")
                break

        if TO_PLOT:
            fig, ax = plt.subplots(2, 1)
            ax[0].plot(env.track)
            ax[0].plot(env.reference, '--')
            ax[1].plot(env.actions)
            plt.show()

    if wandb.run is not None:
        run.finish()


if __name__ == "__main__":
    main(TO_PLOT=True)
