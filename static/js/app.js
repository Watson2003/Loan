document.addEventListener("DOMContentLoaded", () => {
    const cibilSlider = document.getElementById("cibil_score");
    const cibilDisplay = document.getElementById("cibil-display");
    const form = document.getElementById("prediction-form");
    const submitBtn = document.getElementById("submit-btn");
    const btnSpinner = submitBtn.querySelector(".btn-loader-spinner");
    const btnText = submitBtn.querySelector(".btn-text");
    
    const resultPlaceholder = document.getElementById("result-placeholder");
    const resultDisplay = document.getElementById("result-display");
    
    // Circle progress variables
    const progressIndicator = document.getElementById("progress-indicator");
    const probabilityDisplay = document.getElementById("probability-display");
    const radius = 55;
    const circumference = 2 * Math.PI * radius; // Approx 345.575
    
    // Initialize Circle Dasharray
    progressIndicator.style.strokeDasharray = `${circumference} ${circumference}`;
    progressIndicator.style.strokeDashoffset = circumference;

    // Update Slider Display on input
    cibilSlider.addEventListener("input", (e) => {
        cibilDisplay.textContent = e.target.value;
    });

    // Helper to animate circular progress ring
    function setProgress(percent) {
        const offset = circumference - (percent / 100) * circumference;
        progressIndicator.style.strokeDashoffset = offset;
    }

    // Form Submission handler
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // Show Loading State
        submitBtn.disabled = true;
        btnSpinner.classList.remove("hidden");
        btnText.textContent = "Analyzing Profile...";
        
        // Read form data
        const formData = {
            no_of_dependents: parseInt(document.getElementById("no_of_dependents").value),
            education: document.getElementById("education").value,
            self_employed: document.getElementById("self_employed").value,
            income_annum: parseFloat(document.getElementById("income_annum").value),
            loan_amount: parseFloat(document.getElementById("loan_amount").value),
            loan_term: parseInt(document.getElementById("loan_term").value),
            cibil_score: parseInt(cibilSlider.value),
            residential_assets_value: parseFloat(document.getElementById("residential_assets_value").value),
            commercial_assets_value: parseFloat(document.getElementById("commercial_assets_value").value),
            luxury_assets_value: parseFloat(document.getElementById("luxury_assets_value").value),
            bank_asset_value: parseFloat(document.getElementById("bank_asset_value").value)
        };

        try {
            const response = await fetch("/api/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errDetail = await response.json();
                throw new Error(errDetail.detail || "Server encountered an error.");
            }

            const result = await response.json();
            
            // Toggle view visibility
            resultPlaceholder.classList.add("hidden");
            resultDisplay.classList.remove("hidden");
            
            // Clean previous status classes
            resultDisplay.classList.remove("approved", "rejected");
            
            // Update decision details
            const isApproved = result.decision === "Approved";
            resultDisplay.classList.add(isApproved ? "approved" : "rejected");
            
            const badge = document.getElementById("decision-badge");
            badge.textContent = result.decision;
            
            // Convert probability to percentage
            const scorePercentage = Math.round(result.probability * 100);
            probabilityDisplay.textContent = `${scorePercentage}%`;
            setProgress(scorePercentage);
            
            // Update Header & Risk Levels
            const riskHeaderTitle = document.getElementById("risk-header-title");
            const riskHeaderDesc = document.getElementById("risk-header-desc");
            
            if (isApproved) {
                if (scorePercentage >= 85) {
                    riskHeaderTitle.textContent = "Very Low Approval Risk";
                    riskHeaderDesc.textContent = "Applicant exhibits premium financial backing and history, indicating a virtually guaranteed approval profile.";
                } else if (scorePercentage >= 65) {
                    riskHeaderTitle.textContent = "Low Approval Risk";
                    riskHeaderDesc.textContent = "Standard low-risk profile. Meets credit specifications with ample asset backing.";
                } else {
                    riskHeaderTitle.textContent = "Moderate Approval Risk";
                    riskHeaderDesc.textContent = "Approved with borderline margins. Recommended to request standard terms or double-check collateral verification.";
                }
            } else {
                const riskPercent = 100 - scorePercentage;
                if (riskPercent >= 85) {
                    riskHeaderTitle.textContent = "Critical Risk Level";
                    riskHeaderDesc.textContent = "Severe warning rating. Very low CIBIL score or lack of asset buffer blocks automatic approval.";
                } else if (riskPercent >= 65) {
                    riskHeaderTitle.textContent = "High Default Risk";
                    riskHeaderDesc.textContent = "Rejected due to baseline requirements mismatch. Leverage higher down payments or co-signers.";
                } else {
                    riskHeaderTitle.textContent = "Borderline Reject Risk";
                    riskHeaderDesc.textContent = "Narrowly failed approval validation. Suggest manually reviewing assets or offering shorter loan terms.";
                }
            }
            
            // Update Metrics Cards
            document.getElementById("lti-display").textContent = `${result.lti_ratio}%`;
            document.getElementById("asset-display").textContent = `${result.asset_cover}x`;
            document.getElementById("cibil-class-display").textContent = result.cibil_status;
            
            // Update custom Recommendations
            const recomList = document.getElementById("recom-list");
            recomList.innerHTML = ""; // Clear
            
            const recommendations = [];
            
            if (isApproved) {
                recommendations.push(`CIBIL rating classified as <strong>${result.cibil_status}</strong> (${formData.cibil_score} points), proving healthy historical credit discipline.`);
                recommendations.push(`Asset coverage factor stands at <strong>${result.asset_cover}x</strong> relative to requested principal, offering solid collateral security.`);
                recommendations.push(`LTI ratio of <strong>${result.lti_ratio}%</strong> indicates requested loan scale fits well within the applicant's annual income capacity.`);
                recommendations.push("<strong>Approved Action:</strong> Proceed to automated underwriting and formal loan contract generation.");
            } else {
                if (formData.cibil_score < 600) {
                    recommendations.push(`CIBIL Score of <strong>${formData.cibil_score}</strong> indicates critical historical repayment issues.`);
                } else {
                    recommendations.push(`CIBIL credit profile is reasonable, but other financial constraints block full automatic clearance.`);
                }
                
                if (result.asset_cover < 1.0) {
                    recommendations.push(`Critical under-collateralization: Asset portfolio ($${(formData.residential_assets_value + formData.commercial_assets_value + formData.luxury_assets_value + formData.bank_asset_value).toLocaleString()}) offers only <strong>${result.asset_cover}x</strong> coverage.`);
                } else {
                    recommendations.push(`Assets offer <strong>${result.asset_cover}x</strong> cover, but high LTI ratio or credit constraints elevate default probabilities.`);
                }
                
                if (result.lti_ratio > 300) {
                    recommendations.push(`Debt-to-income loading is high: Loan size is <strong>${result.lti_ratio}%</strong> of annual income.`);
                }
                
                recommendations.push("<strong>Rejected Action:</strong> Reject or require a co-signer, increased down-payment, or manual credit override.");
            }
            
            recommendations.forEach(recomText => {
                const li = document.createElement("li");
                li.innerHTML = recomText;
                recomList.appendChild(li);
            });
            
            // Smooth scroll to results on mobile/tablets
            if (window.innerWidth <= 992) {
                resultDisplay.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error(error);
            alert(`Error running prediction: ${error.message}`);
        } finally {
            // Restore Button State
            submitBtn.disabled = false;
            btnSpinner.classList.add("hidden");
            btnText.textContent = "Analyze Approval Probability";
        }
    });
});
