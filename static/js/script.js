// Career Cosmos ATS Enhancement Tool - Enhanced JavaScript with HR Evaluation

let currentAnalysisData = null
let currentAnalysisId = null

document.addEventListener("DOMContentLoaded", () => {
  initializeApp()
})

function initializeApp() {
  const analysisForm = document.getElementById("analysisForm")
  if (analysisForm) {
    analysisForm.addEventListener("submit", handleAnalysis)
  }

  // File upload handling
  const fileInput = document.getElementById("resume_file")
  if (fileInput) {
    fileInput.addEventListener("change", handleFileSelect)
  }

  // Text area handling
  const resumeText = document.getElementById("resume_text")
  const resumeFile = document.getElementById("resume_file")

  if (resumeText && resumeFile) {
    resumeText.addEventListener("input", () => {
      if (resumeText.value.trim()) {
        resumeFile.value = ""
        updateFileLabel("Choose File (PDF, DOCX, TXT - Max 16MB)")
      }
    })
  }

  // Initialize tooltips and animations
  initializeAnimations()
}

function handleFileSelect(event) {
  const file = event.target.files[0]
  const label = event.target.nextElementSibling

  if (file) {
    // Validate file type
    if (!validateFileType(file)) {
      showAlert("Invalid file type. Please upload PDF, DOCX, or TXT files only.", "error")
      event.target.value = ""
      return
    }

    // Validate file size
    if (file.size > 16 * 1024 * 1024) {
      showAlert("File size must be less than 16MB", "error")
      event.target.value = ""
      return
    }

    updateFileLabel(`<i class="fas fa-file-check"></i> ${file.name} (${formatFileSize(file.size)})`)
    label.style.color = "#28a745"

    // Clear text area when file is selected
    const textArea = document.getElementById("resume_text")
    if (textArea) {
      textArea.value = ""
    }
  } else {
    updateFileLabel("Choose File (PDF, DOCX, TXT - Max 16MB)")
    label.style.color = ""
  }
}

function updateFileLabel(text) {
  const label = document.querySelector(".file-upload-label")
  if (label) {
    label.innerHTML = text
  }
}

async function handleAnalysis(event) {
  event.preventDefault()

  const formData = new FormData(event.target)

  // Enhanced validation
  const errors = validateForm(formData)
  if (errors.length > 0) {
    showAlert(errors.join("<br>"), "error")
    return
  }

  // Show loading for HR evaluation
  showLoading(true, "Getting professional HR evaluation...")

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: formData,
    })

    const data = await response.json()

    if (data.success) {
      currentAnalysisData = data
      currentAnalysisId = data.analysis_id
      
      // Step 1: Show HR Evaluation
      displayHREvaluation(data.hr_evaluation)
      
      // Store ATS data for later use
      window.atsAnalysisData = data.ats_analysis
      window.atsEvaluationData = data.ats_evaluation
      
      showAlert("HR evaluation completed! Review the assessment below.", "success")
    } else {
      showAlert(data.error || "Analysis failed", "error")
    }
  } catch (error) {
    console.error("Analysis error:", error)
    showAlert("Network error. Please try again.", "error")
  } finally {
    showLoading(false)
  }
}

function displayHREvaluation(hrEvaluation) {
  const hrSection = document.getElementById("hrEvaluation")
  const hrText = document.getElementById("hrEvaluationText")
  
  // Format HR evaluation text
  const formattedEvaluation = hrEvaluation
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>")
    .replace(/(\d+\.)/g, "<br><strong>$1</strong>")
  
  hrText.innerHTML = `<div class="hr-evaluation-content">${formattedEvaluation}</div>`
  
  // Show HR evaluation section
  hrSection.style.display = "block"
  hrSection.classList.add("fade-in")
  hrSection.scrollIntoView({ behavior: "smooth" })
}

function showATSAnalysis() {
  if (!window.atsAnalysisData || !window.atsEvaluationData) {
    showAlert("ATS analysis data not available", "error")
    return
  }

  showLoading(true, "Preparing ATS analysis...")

  setTimeout(() => {
    const atsSection = document.getElementById("atsAnalysis")
    
    // Update ATS scores and analysis
    displayATSResults(window.atsAnalysisData, window.atsEvaluationData)
    
    // Show ATS analysis section
    atsSection.style.display = "block"
    atsSection.classList.add("fade-in")
    atsSection.scrollIntoView({ behavior: "smooth" })
    
    showLoading(false)
    showAlert("ATS analysis ready! You can now generate an enhanced resume.", "success")
  }, 1000)
}

function displayATSResults(atsAnalysis, atsEvaluation) {
  // Update main score with animation
  updateScoreCircle(atsAnalysis.total_score)

  // Update score breakdown
  updateScoreBreakdown(atsAnalysis)

  // Update keyword analysis
  updateKeywordAnalysis(atsAnalysis)

  // Update ATS evaluation text
  const atsEvaluationText = document.getElementById("atsEvaluationText")
  const formattedEvaluation = atsEvaluation
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>")
    .replace(/(\d+\.)/g, "<br><strong>$1</strong>")
  
  atsEvaluationText.innerHTML = `<div class="ats-evaluation-content">${formattedEvaluation}</div>`
}

function updateScoreCircle(score) {
  const scoreElement = document.getElementById("totalScore")
  const circle = scoreElement.closest(".score-circle")

  // Animate score counting
  animateNumber(scoreElement, 0, score, 1500)

  // Update circle progress with color coding
  setTimeout(() => {
    let color = "#dc3545" // Red for low scores
    if (score >= 80)
      color = "#28a745" // Green for high scores
    else if (score >= 60) color = "#ffc107" // Yellow for medium scores

    circle.style.background = `conic-gradient(${color} 0deg, ${color} ${score * 3.6}deg, #e9ecef ${score * 3.6}deg)`
  }, 500)
}

function updateScoreBreakdown(analysis) {
  const scores = [
    { id: "keywordScore", value: "keywordValue", score: analysis.keyword_score },
    { id: "formatScore", value: "formatValue", score: analysis.format_score },
    { id: "contentScore", value: "contentValue", score: analysis.content_score },
    { id: "lengthScore", value: "lengthValue", score: analysis.length_score },
  ]

  scores.forEach((item, index) => {
    const fillElement = document.getElementById(item.id)
    const valueElement = document.getElementById(item.value)

    // Animate progress bar with delay
    setTimeout(
      () => {
        fillElement.style.width = `${item.score}%`
      },
      500 + index * 200,
    )

    // Animate number
    setTimeout(
      () => {
        animateNumber(valueElement, 0, item.score, 1000, "%")
      },
      500 + index * 200,
    )
  })
}

function updateKeywordAnalysis(analysis) {
  const keywordAnalysis = document.getElementById("keywordAnalysis")

  const html = `
        <div class="keyword-stats">
            <div class="keyword-stat">
                <div class="keyword-stat-number">${analysis.matched_keywords.length}</div>
                <div class="keyword-stat-label">Matched</div>
            </div>
            <div class="keyword-stat">
                <div class="keyword-stat-number">${analysis.total_keywords}</div>
                <div class="keyword-stat-label">Total</div>
            </div>
        </div>
        
        <div class="keyword-list">
            <h4><i class="fas fa-check-circle" style="color: #28a745;"></i> Matched Keywords</h4>
            <div class="keyword-tags">
                ${
                  analysis.matched_keywords.length > 0
                    ? analysis.matched_keywords.map((keyword) => `<span class="keyword-tag">${keyword}</span>`).join("")
                    : '<span class="no-keywords">No keywords matched</span>'
                }
            </div>
        </div>
        
        ${
          analysis.missing_keywords.length > 0
            ? `
        <div class="keyword-list">
            <h4><i class="fas fa-exclamation-circle" style="color: #dc3545;"></i> Missing Keywords (Top 15)</h4>
            <div class="keyword-tags">
                ${analysis.missing_keywords
                  .slice(0, 15)
                  .map((keyword) => `<span class="keyword-tag missing">${keyword}</span>`)
                  .join("")}
            </div>
        </div>
        `
            : ""
        }
    `

  keywordAnalysis.innerHTML = html
}

async function generateEnhancedResume() {
  if (!currentAnalysisId) {
    showAlert("Please complete the analysis first", "error")
    return
  }

  showLoading(true, "Generating AI enhanced resume based on HR evaluation and ATS analysis...")

  try {
    const response = await fetch("/enhance_resume", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        analysis_id: currentAnalysisId,
      }),
    })

    const data = await response.json()

    if (data.success) {
      displayEnhancedResume(data.enhanced_resume)
      showAlert("Enhanced resume generated successfully!", "success")
    } else {
      showAlert(data.error || "Enhancement failed", "error")
    }
  } catch (error) {
    console.error("Enhancement error:", error)
    showAlert("Network error. Please try again.", "error")
  } finally {
    showLoading(false)
  }
}

function displayEnhancedResume(enhancedText) {
  const section = document.getElementById("enhancedResumeSection")
  const content = document.getElementById("enhancedResumeText")

  // Format the enhanced resume text
  const formattedText = enhancedText
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>")

  content.innerHTML = `<div class="enhanced-content">${formattedText}</div>`
  
  section.style.display = "block"
  section.classList.add("fade-in")
  section.scrollIntoView({ behavior: "smooth" })
}

async function downloadPDF() {
  if (!currentAnalysisId) {
    showAlert("No enhanced resume available", "error")
    return
  }

  showLoading(true, "Generating PDF...")

  try {
    window.location.href = `/download_enhanced_resume/${currentAnalysisId}`
    showAlert("PDF download started!", "success")
  } catch (error) {
    console.error("PDF download error:", error)
    showAlert("Download failed. Please try again.", "error")
  } finally {
    showLoading(false)
  }
}

function animateNumber(element, start, end, duration, suffix = "") {
  const startTime = performance.now()

  function update(currentTime) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)

    const current = Math.floor(start + (end - start) * easeOutCubic(progress))
    element.textContent = current + suffix

    if (progress < 1) {
      requestAnimationFrame(update)
    }
  }

  requestAnimationFrame(update)
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3)
}

function showLoading(show, text = "Processing...") {
  const loading = document.getElementById("loading")
  const loadingText = document.getElementById("loadingText")

  if (loadingText) {
    loadingText.textContent = text
  }

  loading.style.display = show ? "flex" : "none"
}

function showAlert(message, type = "info") {
  // Remove existing alerts
  const existingAlerts = document.querySelectorAll(".alert")
  existingAlerts.forEach((alert) => alert.remove())

  // Create alert element
  const alert = document.createElement("div")
  alert.className = `alert alert-${type}`
  alert.innerHTML = `
        <i class="fas fa-${type === "error" ? "exclamation-circle" : type === "success" ? "check-circle" : "info-circle"}"></i>
        <span>${message}</span>
        <button class="alert-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `

  // Add to page
  document.body.appendChild(alert)

  // Auto remove after 7 seconds for longer messages
  setTimeout(() => {
    if (alert.parentElement) {
      alert.remove()
    }
  }, 7000)
}

function downloadReport() {
  if (!currentAnalysisData) {
    showAlert("Please run an analysis first", "error")
    return
  }

  const atsAnalysis = currentAnalysisData.ats_analysis
  const hrEvaluation = currentAnalysisData.hr_evaluation
  const atsEvaluation = currentAnalysisData.ats_evaluation

  const reportData = {
    timestamp: new Date().toLocaleString(),
    ats_score: atsAnalysis.total_score,
    keyword_score: atsAnalysis.keyword_score,
    format_score: atsAnalysis.format_score,
    content_score: atsAnalysis.content_score,
    length_score: atsAnalysis.length_score,
    matched_keywords: atsAnalysis.matched_keywords.join(", "),
    missing_keywords: atsAnalysis.missing_keywords.slice(0, 15).join(", "),
    hr_evaluation: hrEvaluation,
    ats_evaluation: atsEvaluation,
  }

  const reportText = `
CAREER COSMOS - COMPREHENSIVE RESUME ANALYSIS REPORT
Generated: ${reportData.timestamp}

========================================
HR PROFESSIONAL EVALUATION
========================================
${reportData.hr_evaluation}

========================================
ATS SCANNER ANALYSIS
========================================
OVERALL ATS SCORE: ${reportData.ats_score}/100

DETAILED SCORES:
- Keyword Match: ${reportData.keyword_score}%
- Format Quality: ${reportData.format_score}%
- Content Quality: ${reportData.content_score}%
- Length Score: ${reportData.length_score}%

KEYWORD ANALYSIS:
Matched Keywords: ${reportData.matched_keywords || "None"}
Missing Keywords: ${reportData.missing_keywords || "None"}

ATS EVALUATION:
${reportData.ats_evaluation}

========================================
Generated by Career Cosmos ATS Enhancement Tool
Visit: https://career-cosmos.com
    `

  const blob = new Blob([reportText], { type: "text/plain" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `Career_Cosmos_Analysis_Report_${new Date().toISOString().split("T")[0]}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  showAlert("Comprehensive analysis report downloaded successfully!", "success")
}

function startNewAnalysis() {
  // Reset form
  document.getElementById("analysisForm").reset()

  // Hide all result sections
  document.getElementById("hrEvaluation").style.display = "none"
  document.getElementById("atsAnalysis").style.display = "none"
  document.getElementById("enhancedResumeSection").style.display = "none"

  // Reset file upload label
  updateFileLabel("Choose File (PDF, DOCX, TXT - Max 16MB)")

  // Clear current data
  currentAnalysisData = null
  currentAnalysisId = null
  window.atsAnalysisData = null
  window.atsEvaluationData = null

  // Scroll to top
  window.scrollTo({ top: 0, behavior: "smooth" })

  showAlert("Ready for new analysis!", "success")
}

function initializeAnimations() {
  // Add fade-in animation class
  const style = document.createElement("style")
  style.textContent = `
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .alert {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            max-width: 450px;
            animation: slideIn 0.3s ease-out;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        
        .alert-info {
            background: #17a2b8;
        }
        
        .alert-success {
            background: #28a745;
        }
        
        .alert-error {
            background: #dc3545;
        }
        
        .alert-close {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            margin-left: auto;
            padding: 0;
            font-size: 1.2rem;
            opacity: 0.8;
        }
        
        .alert-close:hover {
            opacity: 1;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .no-keywords {
            color: #666;
            font-style: italic;
        }

        .hr-evaluation-content, .ats-evaluation-content, .enhanced-content {
            line-height: 1.8;
        }

        .hr-evaluation-content strong, .ats-evaluation-content strong, .enhanced-content strong {
            color: var(--primary-color);
        }

        .evaluation-text {
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            border-left: 4px solid var(--primary-color);
            margin: 1rem 0;
        }
    `
  document.head.appendChild(style)
}

// Utility functions
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

function validateFileType(file) {
  const allowedTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
  ]
  return allowedTypes.includes(file.type)
}

// Enhanced form validation
function validateForm(formData) {
  const errors = []

  const jobDescription = formData.get("job_description")
  if (!jobDescription || jobDescription.trim().length < 50) {
    errors.push("Job description must be at least 50 characters long")
  }

  const resumeFile = formData.get("resume_file")
  const resumeText = formData.get("resume_text")

  if (resumeFile && resumeFile.size > 0) {
    if (!validateFileType(resumeFile)) {
      errors.push("Invalid file type. Please upload PDF, DOCX, or TXT files only")
    }
    if (resumeFile.size > 16 * 1024 * 1024) {
      errors.push("File size must be less than 16MB")
    }
  } else if (!resumeText || resumeText.trim().length < 100) {
    errors.push("Resume text must be at least 100 characters long")
  }

  if (resumeFile && resumeFile.size > 0 && resumeText && resumeText.trim()) {
    errors.push("Please use either file upload OR text input, not both")
  }

  return errors
}
