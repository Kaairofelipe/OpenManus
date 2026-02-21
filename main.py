import argparse
import asyncio

from app.agent.manus import Manus
from app.config import config
from app.logger import logger


def _has_valid_llm_key() -> bool:
    llm_cfg = config.llm.get("default")
    api_key = (llm_cfg.api_key or "").strip() if llm_cfg else ""
    invalid_values = {
        "",
        "YOUR_API_KEY",
        "AZURE API KEY",
        "your Jiekou.AI api key",
    }
    return api_key not in invalid_values and "YOUR_" not in api_key


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Manus agent with a prompt")
    parser.add_argument(
        "--prompt", type=str, required=False, help="Input prompt for the agent"
    )
    args = parser.parse_args()
    if not _has_valid_llm_key():
        logger.error(
            "Invalid API key in config/config.toml. Update [llm].api_key before running OpenManus."
        )
        return

    # Create and initialize Manus agent
    agent = await Manus.create()
    try:
        # Use command line prompt if provided, otherwise ask for input
        prompt = args.prompt if args.prompt else input("Enter your prompt: ")
        if not prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        logger.warning("Processing your request...")
        await agent.run(prompt)
        logger.info("Request processing completed.")
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")
    finally:
        # Ensure agent resources are cleaned up before exiting
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
