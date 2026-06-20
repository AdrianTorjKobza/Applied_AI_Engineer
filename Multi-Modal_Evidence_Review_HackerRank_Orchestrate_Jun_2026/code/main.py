# This module reads rows sequentially from dataset/claims.csv, loops through any attached images for Stage 1 visual analysis,
# maps corporate profile datasets into the context, executes the Stage 2 logical decision reasoning engine, and exports the final predictions dataset to output.csv.

# code/main.py
import os
import pandas as pd
from data_loader import ChallengeDataLoader
from vlm_agent import VLMAgent
from logic_agent import LogicAgent
from models import FinalClaimOutput

def main():
    print("🚀 Initializing Production Claim Verification Engine (Optimized Native Mode)...")
    
    dataset_dir = "../dataset"
    input_claims_path = os.path.join(dataset_dir, "claims.csv")
    output_claims_path = "../output.csv"
    
    if not os.path.exists(input_claims_path):
        print(f"❌ Error: Core input dataset missing at {input_claims_path}")
        return

    # Initialize reference caches
    loader = ChallengeDataLoader(dataset_dir=dataset_dir)
    loader.load_reference_data()
    
    # Establish agents targeting separate local weight groups
    vlm_agent = VLMAgent(model_name="qwen2.5vl:7b")
    logic_agent = LogicAgent(model_name="qwen2.5:7b")
    
    df_claims = pd.read_csv(input_claims_path)
    total_rows = len(df_claims)
    print(f"📋 Loaded {total_rows} production rows for evaluation processing.\n")
    
    # ------------------------------------------------------------
    # PASS 1: Sequential Visual Feature Extraction Phase
    # ------------------------------------------------------------
    print("👁️ Starting Pass 1: Visual Feature Extraction Phase...")
    vlm_cache = {}
    
    for idx, row in df_claims.iterrows():
        user_claim = str(row['user_claim'])
        image_paths_str = str(row['image_paths'])
        image_list = [img.strip() for img in image_paths_str.split(';') if img.strip()]
        
        print(f"   👉 [Claim {idx + 1}/{total_rows}] Scanning visual evidence files...")
        row_vlm_results = []
        for img_filename in image_list:
            full_image_path = os.path.join(dataset_dir, img_filename)
            insight = vlm_agent.process_image(full_image_path, user_claim)
            
            # --- PROACTIVE SILENT FAILURE DETECTION ---
            justification = insight.visual_justification
            if "Image load failure" in justification or "VLM Text Generation Error" in justification:
                print(f"      ⚠️  WARNING: Failed to process {img_filename}!")
                print(f"          Reason: {justification}")
            else:
                # Optional: Print a success checkmark for visual confirmation
                print(f"      ✅ Successfully analyzed {img_filename}")
            # ------------------------------------------

            row_vlm_results.append(insight)
            
        vlm_cache[idx] = row_vlm_results

    # ------------------------------------------------------------
    # PASS 2: Token-Optimized Analytical Logic Synthesis Phase
    # ------------------------------------------------------------
    print("\n🧠 Starting Pass 2: Policy Logic & Corporate Rule Synthesis Phase...")
    production_records = []
    
    for idx, row in df_claims.iterrows():
        print(f"   👉 [Claim {idx + 1}/{total_rows}] Evaluating rules & user risk profile...")
        user_id = str(row['user_id'])
        user_claim = str(row['user_claim'])
        claim_object = str(row['claim_object'])
        image_paths_str = str(row['image_paths'])
        
        user_history = loader.get_user_context(user_id)
        requirements = loader.get_requirements_for_object(claim_object)
        cached_vlm_insights = vlm_cache[idx]
        
        analysis = logic_agent.synthesize_claim(
            user_id=user_id,
            user_claim=user_claim,
            claim_object=claim_object,
            image_paths=image_paths_str,
            vlm_results=cached_vlm_insights,
            user_history=user_history,
            requirements=requirements
        )
        
        # Intercept lists and convert them to semicolon-separated strings
        raw_supporting_ids = analysis.get("supporting_image_ids", "none")
        if isinstance(raw_supporting_ids, list):
            clean_supporting_ids = ";".join([str(x) for x in raw_supporting_ids])
        else:
            clean_supporting_ids = str(raw_supporting_ids)

        full_row = {
            "user_id": user_id,
            "image_paths": image_paths_str,
            "user_claim": user_claim,
            "claim_object": claim_object,
            "evidence_standard_met": analysis.get("evidence_standard_met", False),
            "evidence_standard_met_reason": analysis.get("evidence_standard_met_reason", "unknown"),
            "risk_flags": analysis.get("risk_flags", "none"),
            "issue_type": analysis.get("issue_type", "unknown"),
            "object_part": analysis.get("object_part", "unknown"),
            "claim_status": analysis.get("claim_status", "not_enough_information"),
            "claim_status_justification": analysis.get("claim_status_justification", ""),
            "supporting_image_ids": analysis.get("supporting_image_ids", "none"),
            "valid_image": analysis.get("valid_image", False),
            "severity": analysis.get("severity", "unknown")
        }
        
        validated_box = FinalClaimOutput(**full_row)
        production_records.append(validated_box.model_dump())

    # Build and align target output CSV columns
    df_output = pd.DataFrame(production_records)
    required_column_order = [
        "user_id", "image_paths", "user_claim", "claim_object",
        "evidence_standard_met", "evidence_standard_met_reason", "risk_flags",
        "issue_type", "object_part", "claim_status", "claim_status_justification",
        "supporting_image_ids", "valid_image", "severity"
    ]
    df_output = df_output[required_column_order]
    df_output.to_csv(output_claims_path, index=False)
    print(f"\n🎉 Production execution complete! Output saved cleanly to: {output_claims_path}")

if __name__ == "__main__":
    main()