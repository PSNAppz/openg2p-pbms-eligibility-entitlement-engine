## Order of Celery Worker Tasks

The following worker tasks are responsible for processing background jobs that have been queued by the beat producers. Each worker handles a specific stage in the eligibility and entitlement workflow, performing the necessary business logic and updating the status of records in the database.

1. **Beneficiary List Worker**
   Processes G2P beneficiary lists with a processing eligibility_process_status. Runs eligibility checks and updates the status to reflect the outcome (e.g., ELIGIBLE, INELIGIBLE, or ERROR).

2. **Entitlement Worker**
   Handles BeneficiaryListDetails with a processing entitlement_process_status. Calculates entitlements for eligible beneficiaries and updates their entitlement records accordingly.

3. **Disbursement Envelope Creation Worker**
   Processes entitlement records that are ready for envelope creation. Generates disbursement envelopes and updates their status to indicate readiness for batch grouping.

4. **Disbursement Batch Creation Worker**
   Groups ready disbursement envelopes into batches. Updates the status of envelopes and batches, and prepares them for the disbursement process.

5. **Disbursement Worker**
   Executes the final disbursement actions for batches that are ready. Updates the status of batches and envelopes to reflect successful or failed disbursement.

---

Each worker task is designed to be idempotent and robust, ensuring that failures can be retried without data corruption. The workers interact with the PBMS, BG Task, and Social Registry databases as needed, and log progress for monitoring and debugging.
