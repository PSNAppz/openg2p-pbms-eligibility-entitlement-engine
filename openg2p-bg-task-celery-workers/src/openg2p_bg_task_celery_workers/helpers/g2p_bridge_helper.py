import asyncio
import uuid
from datetime import datetime, timezone

import requests
from openg2p_bg_task_models.schemas import Disbursement
from openg2p_fastapi_common.utils.crypto import KeymanagerCryptoHelper
from openg2p_g2p_bridge_models.schemas import (
    DisbursementEnvelopeRequest,
    DisbursementEnvelopeRequestBody,
    DisbursementEnvelopeResponse,
    DisbursementPayload,
    DisbursementRequest,
    DisbursementRequestBody,
    DisbursementResponse,
    G2PRequestHeader,
)


class G2PBridgeDisbursementHelper:
    def __init__(self, config, logger):
        self._config = config
        self._logger = logger
        self.keymanager_crypto_helper = KeymanagerCryptoHelper()

    def create_disbursement_envelopes(self, disbursement_envelope_request_message):
        """
        Sends a request to the bridge to create a disbursement envelope.
        """
        disbursement_envelope_request_header = G2PRequestHeader(
            sender_app_mnemonic=self._config.keymanager_sign_app_id,
            sender_app_url="",
            request_id=uuid.uuid4().hex,
            request_timestamp=datetime.now(timezone.utc).isoformat(),
            instance_id="string",
        )
        disbursement_envelope_request_body = DisbursementEnvelopeRequestBody(
            request_payload=disbursement_envelope_request_message
        )
        disbursement_envelope_request = DisbursementEnvelopeRequest(
            request_header=disbursement_envelope_request_header,
            request_body=disbursement_envelope_request_body,
        )
        disbursement_envelope_request_json = disbursement_envelope_request.model_dump(
            mode="json"
        )
        self._logger.debug(
            f"Disbursement Envelope Request: {disbursement_envelope_request_json}"
        )

        envelope_creation_url = (
            self._config.g2p_bridge_base_url + "/create_disbursement_envelopes"
        )
        self._logger.debug(f"Envelope Creation URL: {envelope_creation_url}")

        jwt_token = asyncio.run(
            self.keymanager_crypto_helper.create_jwt_token(
                payload=disbursement_envelope_request_json,
                include_payload=False,
                include_certificate=False,
                include_cert_hash=False,
                km_app_id=self._config.keymanager_sign_app_id,
                km_ref_id=self._config.keymanager_sign_ref_id,
            )
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Signature": jwt_token,
        }

        self._logger.info("Calling disbursement envelope creation endpoint")
        try:
            response = requests.post(
                envelope_creation_url,
                json=disbursement_envelope_request_json,
                headers=headers,
            )
            response.raise_for_status()
            self._logger.info(
                f"Response status code for disbursement envelope request: {response.status_code}"
            )
            disbursement_envelope_response = (
                DisbursementEnvelopeResponse.model_validate(response.json())
            )
            self._logger.debug(
                f"Disbursement Envelope Response: {disbursement_envelope_response}"
            )

            return disbursement_envelope_response, None

        except Exception as e:
            self._logger.error(
                f"Error occurred while calling envelope creation API: {e}"
            )
            return None, str(e)

    def create_disbursement(self, disbursement_batch, bg_task_session, narrative):
        """
        Sends a request to the bridge to create disbursements.
        """

        disbursement_payloads = []

        for disbursement in disbursement_batch.disbursements:
            disbursement = Disbursement(**disbursement)

            disbursement_payload = DisbursementPayload(
                disbursement_id=disbursement.disbursement_id,
                disbursement_envelope_id=disbursement_batch.disbursement_envelope_id,
                beneficiary_id=disbursement.beneficiary_id,
                beneficiary_name=None,
                disbursement_quantity=disbursement.entitlement,
                compute_elements=disbursement.compute_elements,
                disbursement_cycle_id=int(disbursement_batch.disbursement_cycle_id),
                disbursement_batch_control_id=disbursement_batch.id,
                narrative=narrative,
            )
            disbursement_payloads.append(disbursement_payload)

        disbursement_header = G2PRequestHeader(
            sender_app_mnemonic=self._config.keymanager_sign_app_id,
            sender_app_url="",
            request_id=uuid.uuid4().hex,
            request_timestamp=datetime.now(timezone.utc).isoformat(),
            instance_id="string",
        )

        disbursement_request_body = DisbursementRequestBody(
            disbursement_batch_control_id=disbursement_batch.id,
            request_payload=disbursement_payloads,
        )

        disbursement_request = DisbursementRequest(
            request_header=disbursement_header,
            request_body=disbursement_request_body,
        )
        disbursement_request_json = disbursement_request.model_dump(mode="json")
        self._logger.debug(f"Disbursement request payload: {disbursement_request_json}")

        disbursement_url = self._config.g2p_bridge_base_url + "/create_disbursements"
        self._logger.debug(f"Disbursement URL: {disbursement_url}")

        jwt_token = asyncio.run(
            self.keymanager_crypto_helper.create_jwt_token(
                payload=disbursement_request_json,
                include_payload=False,
                include_certificate=False,
                include_cert_hash=False,
                km_app_id=self._config.keymanager_sign_app_id,
                km_ref_id=self._config.keymanager_sign_ref_id,
            )
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Signature": jwt_token,
        }
        self._logger.info(
            f"Calling disbursement creation endpoint for disbursement batch id {disbursement_batch.id} having {len(disbursement_payloads)} beneficiaries"
        )
        try:
            response = requests.post(
                disbursement_url, json=disbursement_request_json, headers=headers
            )
            response.raise_for_status()
            self._logger.info(
                f"Response status code for disbursement batch id {disbursement_batch.id}: {response.status_code}"
            )

            disbursement_response = DisbursementResponse.model_validate(response.json())
            self._logger.debug(
                f"Response for disbursement batch id {disbursement_batch.id}: {disbursement_response}"
            )

            return disbursement_response, None

        except Exception as e:
            self._logger.error(f"Error occurred while calling disbursement API: {e}")
            return None, str(e)
