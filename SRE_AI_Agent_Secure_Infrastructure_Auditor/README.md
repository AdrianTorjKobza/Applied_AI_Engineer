# SRE AI Agent: Secure Infrastructure Auditor

## 📖 Overview
The **SRE AI Agent** is an autonomous, air-gapped Site Reliability Engineering assistant powered by local Large Language Models (LLMs). Designed to operate within secure Kubernetes environments, it actively analyzes infrastructure telemetry, diagnoses system anomalies (such as CrashLoopBackOff states or CPU starvation), and provides actionable remediation steps.

This project emphasizes enterprise-grade security, utilizing an identity-first approach where the AI agent must authenticate via Keycloak and HashiCorp Vault before executing its diagnostic routines.

---

## 🎯 Use Case
Modern Kubernetes environments generate overwhelming amounts of telemetry data. When an incident occurs (e.g., a checkout service timing out), SREs must manually correlate metrics, logs, and cluster state to find the root cause. 

This AI Agent automates the "Level 1/Level 2" diagnostic triage:
1. **Securely Authenticates:** Proves its identity to the cluster via OIDC/JWT.
2. **Observes:** Queries infrastructure metrics (Prometheus).
3. **Reasons:** Uses a LangGraph state machine and a local LLM to analyze the context.
4. **Reports:** Outputs a human-readable root-cause analysis and recommended fix.

---

## 🛠️ Tech Stack
* **AI & Orchestration:** * [Ollama](https://ollama.com/) (Local Llama 3 Model)
  * [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/) (State Machine & Agent Logic)
  * [LangChain](https://python.langchain.com/)
* **Security & Identity:** * [Keycloak](https://www.keycloak.org/) (OIDC Identity Provider)
  * [HashiCorp Vault](https://www.vaultproject.io/) (Dynamic Secrets Management)
* **Observability:** * Prometheus (Architecture target, currently mocked for local execution)
* **Infrastructure as Code (IaC):** * Terraform
  * Kubernetes (Local Docker Desktop)
* **Language & Config:** * Python 3.11+
  * `pydantic-settings` (Type-safe environment validation)

---

## 🏛️ High-Level Architecture (Hybrid Local Setup)

Due to hardware constraints typical of local Docker Desktop deployments, this architecture utilizes a **Hybrid Execution Model**. The heavy security infrastructure runs inside the Kubernetes cluster, while the Agent's AI logic and LLM run directly on the host machine to preserve RAM and prevent networking timeouts.

### Execution Flow:
1. **The Handshake (Keycloak):** The Python Agent requests a JWT from the Kubernetes-hosted Keycloak server using Client Credentials (`client_id` and `client_secret`).
2. **The Exchange (Vault):** The Agent presents the JWT to HashiCorp Vault. Vault validates the token's signature with Keycloak and issues a temporary Vault Token to the Agent.
3. **The Observation (Prometheus):** The Agent gathers infrastructure state. *(Currently mocked in `agent.py` to prevent local cluster resource exhaustion).*
4. **The Brain (Ollama):** The LangGraph engine feeds the authenticated state and infrastructure telemetry into the local Ollama LLM to deduce the root cause of the simulated outage.

---

## ⚠️ Constraints & Limitations (Local Environment)

Building secure, enterprise infrastructure on a single local machine requires specific architectural compromises:

1. **Air-Gapped LLM Execution:** Originally intended to use OpenAI, the project pivoted to local **Ollama (Llama 3)** to bypass corporate proxy SSL intercept issues and API quota limits. This guarantees 100% data privacy.
2. **Mocked Observability Layer:** The `kube-prometheus-stack` Helm chart is heavily resource-intensive. To prevent Docker Desktop from timing out during the `pre-install` webhook phase, the Prometheus deployment (`observability.tf`) is currently disabled. The Python agent utilizes a mocked data dictionary to simulate cluster anomalies.
3. **Windows Networking Quirks:** To bypass Windows IPv6 `localhost` routing errors (`WinError 10049`), all API endpoints are explicitly hardcoded to IPv4 (`127.0.0.1`) in the `.env` configuration.
4. **Port-Forwarding Dependency:** Because the Agent runs outside the cluster, it relies on background `kubectl port-forward` tunnels to communicate with Keycloak (8080) and Vault (8200).

---

## 📂 File Structure

```text
SRE_AI_Agent_Secure_Infrastructure_Auditor/
│
├── src/
│   ├── main.py           # Core execution loop and entry point for the SRE Agent
│   ├── agent.py          # LangGraph Nodes, State Machine, and AI thought processes
│   ├── schema.py         # Type definitions, Pydantic models, and AgentState definitions
│   ├── config.py         # Pydantic Settings class for type-safe environment variables
│   └── debug_auth.py     # Sandbox script to test Keycloak/Vault authentication isolation
│
├── .env                  # (GitIgnored) Local host endpoints and secret Keycloak credentials
├── .gitignore            # Prevents committing .env, tfstate, and venv files
│
├── main.tf               # Terraform core providers and cluster bootstrapping
├── variables.tf          # Terraform variable definitions
├── outputs.tf            # Terraform outputs (e.g., Keycloak Client Secret)
├── security.tf           # Keycloak & Vault Kubernetes deployment manifests
├── agent.tf.disabled     # Quarantined Kubernetes deployment for the LangGraph agent
└── observability.tf.disabled # Quarantined Prometheus Helm chart deployment
│
└── README.md             # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Environment & Dependency Setup
Before running the infrastructure or the agent, prepare your local Python environment on your host machine:

```powershell
# Clone the repository (if not already inside it)
cd C:\ATK\1.GitHub\SRE_AI_Agent_Secure_Infrastructure_Auditor

# Create an isolated Python virtual environment
python -m venv venv

# Activate the virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# Upgrade pip to the latest version
python -m pip install --upgrade pip

# Install the required dependencies
pip install pydantic-settings python-dotenv requests langgraph langchain-ollama
```

### 2. Deploy the Security Infrastructure
Deploy Keycloak and HashiCorp Vault to your local Kubernetes cluster using Terraform:

```powershell
# Initialize Terraform providers
terraform init

# Target the core security namespace and deployments first to prevent resource timeouts
terraform apply -target "kubernetes_namespace_v1.security" -target "kubernetes_deployment.keycloak" -target "kubernetes_service.keycloak" -target "helm_release.vault" -auto-approve

# Wait until the pods are in a 'Running' state (kubectl get pods -n security)
# Then, open two separate PowerShell windows to establish background network tunnels:
# Window 1:
kubectl port-forward svc/keycloak 8080:8080 -n security
# Window 2:
kubectl port-forward svc/vault 8200:8200 -n security

# Return to your main terminal and apply the remaining configuration (Realms, Clients, Policies)
terraform apply -auto-approve
```

### 3. Configure Environment Secrets
Extract the auto-generated Keycloak secret from Terraform and map it to your local environment file:

```powershell
# Fetch the client secret generated by the Keycloak provider
terraform output keycloak_client_secret
```

Create a file named `.env` in the root directory (`C:\ATK\1.GitHub\SRE_AI_Agent_Secure_Infrastructure_Auditor\.env`) and populate it with your configuration:

```env
KEYCLOAK_URL=[http://127.0.0.1:8080](http://127.0.0.1:8080)
VAULT_URL=[http://127.0.0.1:8200](http://127.0.0.1:8200)
OLLAMA_URL=[http://127.0.0.1:11434](http://127.0.0.1:11434)
CLIENT_ID=langgraph-api
CLIENT_SECRET=PASTE_YOUR_TERRAFORM_OUTPUT_SECRET_HERE
```

### 4. Keycloak Identity Provider Hardening
Because Keycloak disables machine-to-machine tokens by default, you must manually authorize the client container to pull tokens without a human login session:

1. Open your browser and navigate to the Keycloak Console: `http://127.0.0.1:8080/admin` (Log in using your admin credentials).
2. Switch the realm workspace via the top-left dropdown from `master` to **`agent-factory`**.
3. Click **Clients** in the left menu sidebar and select **`langgraph-api`**.
4. In the **Capability Config** section, find the **Service accounts enabled** switch and toggle it to **ON**.
5. Scroll to the bottom and click **Save**.

### 5. Launch the SRE Agent
Ensure your local Ollama instance is running (`ollama run llama3`), verify your background tunnels are active, and start the graph state machine:

```powershell
python src/agent.py
```

## 🔮 Recommended Future Improvements

1. **Implement Agent "Tools" (Execution Layer):** Evolve the agent from a passive *diagnoser* to an active *remediator* by adding a `node_execute_tool` to the LangGraph. Equip it with Python functions to run `kubectl get pods`, `kubectl logs`, or `kubectl rollout restart`.
2. **Re-Enable Real Prometheus:** Migrate the cluster to a more capable machine (or a cloud provider) to re-enable `observability.tf` and swap the mock data in `agent.py` for live PromQL queries.
3. **Containerize the Agent:** Create a `Dockerfile` for the Python application so it can be deployed directly into the Kubernetes cluster alongside Keycloak, eliminating the need for local `.env` files and `kubectl port-forward` tunnels.