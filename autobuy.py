import pexpect
import argparse
import time
import logging

def setup_logger():
    logger = logging.getLogger("subnet_registration")
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs all levels
    fh = logging.FileHandler("registration_log.txt")
    fh.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def register_subnet(net_uid, wallet_name, hotkey_name, network, password, max_cost, logger):
    while True:
        command = f"btcli subnets register --netuid {net_uid} --wallet.name {wallet_name} --wallet.hotkey {hotkey_name} --subtensor.chain_endpoint ws://subtensor.local:9944"
        try:
            process = pexpect.spawn(command, encoding='utf-8')
            process.expect("Do you want to continue", timeout=300)
            process.sendline("y")
            process.expect("Enter password to unlock key:", timeout=300)
            process.sendline(password)
            output_before_recycle_raw = process.before
            output_before_recycle = ''.join(ch for ch in output_before_recycle_raw if ch.isprintable())
            logger.debug(f"Output before expecting recycle pattern: {output_before_recycle}")
            process.expect("Recycle τ(\d+\.\d+) to register on subnet", timeout=300)
            logger.debug("Found Recycle pattern")
            recycle_cost = float(process.match.group(1))
            logger.info(f"Recycle cost: τ{recycle_cost}")
            if recycle_cost > max_cost:
                logger.warning(f"Recycle cost τ{recycle_cost} exceeds max cost τ{max_cost}. Stopping.")
                break
            else:
                process.sendline("y")
                index = process.expect(["Registered", "❌ Failed:", pexpect.TIMEOUT], timeout=300)
                output = process.before  # Get the output before the match
                logger.info(output)
                if index == 0:
                    logger.info("Registration successful!")
                    break
                elif index == 1:
                    logger.error("Registration failed. Retrying...")
                    time.sleep(5)  # Wait for a while before retrying
                    process.close()  # Close the previous process before retrying
                else:
                    logger.error("Timeout occurred. Retrying...")
                    process.kill()
                    time.sleep(5)  # Wait for a while before retrying
        except pexpect.exceptions.EOF:
            logger.error("EOF (End Of File) encountered. Retrying...")
            time.sleep(5)  # Wait for a while before retrying

def main():
    parser = argparse.ArgumentParser(description="Auto register subnet")
    parser.add_argument("--net_uid", type=str, help="Net UID")
    parser.add_argument("--wallet_name", type=str, help="Wallet name")
    parser.add_argument("--hotkey_name", type=str, help="Hotkey name")
    parser.add_argument("--network", type=str, help="Network")
    parser.add_argument("--password", type=str, help="Password")
    parser.add_argument("--max_cost", type=float, help="Max cost")
    args = parser.parse_args()

    logger = setup_logger()
    logger.info("Starting subnet registration process...")
    logger.info(f"Net UID: {args.net_uid}, Wallet Name: {args.wallet_name}, Hotkey Name: {args.hotkey_name}, Network: {args.network}, Max Cost: τ{args.max_cost}")

    register_subnet(args.net_uid, args.wallet_name, args.hotkey_name, args.network, args.password, args.max_cost, logger)

    logger.info("Subnet registration process completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto register subnet")
    parser.add_argument("--net_uid", type=str, help="Net UID")
    parser.add_argument("--wallet_name", type=str, help="Wallet name")
    parser.add_argument("--hotkey_name", type=str, help="Hotkey name")
    parser.add_argument("--network", type=str, help="Network")
    parser.add_argument("--password", type=str, help="Password")
    parser.add_argument("--max_cost", type=float, help="Max cost")
    args = parser.parse_args()

    logger = setup_logger()
    logger.info("Starting subnet registration process...")
    logger.info(f"Net UID: {args.net_uid}, Wallet Name: {args.wallet_name}, Hotkey Name: {args.hotkey_name}, Network: {args.network}, Max Cost: τ{args.max_cost}")

    register_subnet(args.net_uid, args.wallet_name, args.hotkey_name, args.network, args.password, args.max_cost, logger)

    logger.info("Subnet registration process completed.")

if __name__ == "__main__":
    main()

