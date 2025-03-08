import yaml
import logging


class ReasonerConfig:
    def __init__(self, file_path):

        self.google_search_key = ""

        self.openai_key = ""

        self.ERGO_ROOT = ""
        self.XSB_DIR = ""

        self.vllm_auth_key = ""

        # key to check signature jwt
        self.jwt_public_key =  ""

        # claim value of "server-authorization" to verify
        self.jwt_server_auth_claim=  ""

        self.load_config(file_path)

    def load_config(self, file_path):
        try:
            with open(file_path, 'r') as file:
                config = yaml.safe_load(file)
                reasoner_config = config.get("vital_llm_reasoner", {})

                self.openai_key = reasoner_config.get("openai_key", "")

                self.google_search_key = reasoner_config.get("google_search_key", "")

                self.vllm_auth_key = reasoner_config.get("vllm_auth_key", "")

                self.jwt_public_key = reasoner_config.get("jwt_public_key", "")
                self.jwt_server_auth_claim = reasoner_config.get("jwt_server_auth_claim", "")

                logic_engine_config = config.get("logic_engine", {})
                self.ERGO_ROOT = logic_engine_config.get('ERGO_ROOT')
                self.XSB_DIR = logic_engine_config.get('XSB_DIR')

                logging.info("Configuration loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Configuration file not found at: {file_path}")
        except yaml.YAMLError as e:
            logging.info(f"Error parsing YAML file: {e}")
