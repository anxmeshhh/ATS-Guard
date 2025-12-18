// Dashboard-specific JavaScript functionality

document.addEventListener("DOMContentLoaded", () => {
  const analysisForm = document.getElementById("analysisForm")
  const loadingIndicator = document.getElementById("loadingIndicator")
  const resultsSection = document.getElementById("resultsSection")

  // Tab functionality
  initializeTabs()

  // Form submission
  if (analysisForm) {
    analysisForm.addEventListener("submit", handleAnalysisSubmission)
  }

  // Action buttons
  initializeActionButtons()
})

function initializeTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn")
  const tabPanes = document.querySelectorAll(".tab-pane")

  tabButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const targetTab = this.getAttribute("data-tab")

      // Remove active class from all buttons and panes
      tabButtons.forEach((btn) => btn.classList.remove("active"))
      tabPanes.forEach((pane) => pane.classList.remove("active"))

      // Add active class to clicked button and corresponding pane
      this.classList.add("active")
      document.getElementById(targetTab).classList.add("active")
    })
  })
}

async function handleAnalysisSubmission(e) {
  e.preventDefault()

  const formData = new FormData(e.target)
  const analyzeBtn = document.getElementById("analyzeBtn")

  // Validate form
  if (!validateAnalysisForm(formData)) {
    return
  }

  // Show loading state
  showLoadingState(true)
  analyzeBtn.disabled = true

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: formData,
    })

    const result = await response.json()

    if (result.success) {
      displayResults(result)
      clearAutoSave("analysisForm")
      showNotification("Analysis completed successfully!", "success")
    } else {
      throw new Error(result.error || "Analysis failed")
    }
  } catch (error) {
    console.error("Analysis error:", error)
    showNotification(error.message || "Analysis failed. Please try again.", "error")
  } finally {
    showLoadingState(false)
    analyzeBtn.disabled = false
  }
}

function validateAnalysisForm(formData) {
  const jobTitle = formData.get("job_title")
  const jobDescription = formData.get("job_description")
  const resumeFile = formData.get("resume_file")

  if (!jobTitle || !jobTitle.trim()) {
    showNotification("Please enter a job title", "error")
    return false
  }

  if (!jobDescription || !jobDescription.trim()) {
    showNotification("Please enter a job description", "error")
    return false
  }

  if (!resumeFile || resumeFile.size === 0) {
    showNotification("Please upload a resume file", "error")
    return false
  }

  // Check file size (16MB limit)
  if (resumeFile.size > 16 * 1024 * 1024) {
    showNotification("File size must be less than 16MB", "error")
    return false
  }

  // Check file type
  const allowedTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
  ]
  if (!allowedTypes.includes(resumeFile.type) && !resumeFile.name.match(/\.(pdf|docx|txt)$/i)) {
    showNotification("Please upload a PDF, DOCX, or TXT file", "error")
    return false
  }

  return true
}

function showLoadingState(show) {
  const loadingIndicator = document.getElementById("loadingIndicator")
  const resultsSection = document.getElementById("resultsSection")

  if (show) {
    loadingIndicator.style.display = "block"
    resultsSection.style.display = "none"
  } else {
    loadingIndicator.style.display = "none"
  }
}

function displayResults(result) {
  const resultsSection = document.getElementById("resultsSection")
  const atsAnalysis = result.ats_analysis
  const aiSuggestions = result.ai_suggestions

  // Update ATS Score
  updateATSScore(atsAnalysis)

  // Update content sections
  updateCorrectionsTab(aiSuggestions.highlighted_corrections)
  updateRewrittenTab(aiSuggestions.rewritten_sections)
  updateKeywordsTab(atsAnalysis)
  updateRecommendationsTab(aiSuggestions.overall_recommendations)

  // Store results for download functionality
  window.currentResults = result

  // Show results section
  resultsSection.style.display = "block"
  resultsSection.scrollIntoView({ behavior: "smooth" })
}

function updateATSScore(atsAnalysis) {
  const scoreElement = document.getElementById("atsScore")
  const scoreBreakdown = document.getElementById("scoreBreakdown")
  const scoreCircle = document.querySelector(".score-circle")

  if (scoreElement) {
    scoreElement.textContent = Math.round(atsAnalysis.overall_score)
  }

  // Update score circle gradient
  if (scoreCircle) {
    const percentage = atsAnalysis.overall_score
    const degrees = (percentage / 100) * 360
    scoreCircle.style.background = `conic-gradient(var(--primary-color) ${degrees}deg, var(--border-color) ${degrees}deg)`
  }

  // Update score breakdown
  if (scoreBreakdown && atsAnalysis.category_scores) {
    scoreBreakdown.innerHTML = ""
    Object.entries(atsAnalysis.category_scores).forEach(([category, data]) => {
      const categoryDiv = document.createElement("div")
      categoryDiv.className = "category-score"
      categoryDiv.innerHTML = `
                <span class="category-name">${category}</span>
                <span class="category-value">${data.score}%</span>
            `
      scoreBreakdown.appendChild(categoryDiv)
    })
  }
}

function updateCorrectionsTab(corrections) {
  const correctionsContent = document.querySelector(".corrections-content")
  if (correctionsContent) {
    correctionsContent.innerHTML = ""
    corrections.forEach((correction) => {
      const correctionDiv = document.createElement("div")
      correctionDiv.className = "correction-item"
      correctionDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <span>${correction}</span>
            `
      correctionsContent.appendChild(correctionDiv)
    })
  }
}

function updateRewrittenTab(rewrittenSections) {
  const rewrittenContent = document.querySelector(".rewritten-content")
  if (rewrittenContent) {
    rewrittenContent.innerHTML = ""
    Object.entries(rewrittenSections).forEach(([section, content]) => {
      const sectionDiv = document.createElement("div")
      sectionDiv.className = "rewritten-section"
      sectionDiv.innerHTML = `
                <h4><i class="fas fa-edit"></i> ${section.charAt(0).toUpperCase() + section.slice(1)}</h4>
                <p>${content}</p>
                <button class="copy-section-btn" onclick="copyToClipboard('${content.replace(/'/g, "\\'")}')">
                    <i class="fas fa-copy"></i> Copy Section
                </button>
            `
      rewrittenContent.appendChild(sectionDiv)
    })
  }
}

function updateKeywordsTab(atsAnalysis) {
  const keywordsContent = document.querySelector(".keywords-content")
  if (keywordsContent) {
    keywordsContent.innerHTML = ""

    // Matched keywords
    if (atsAnalysis.matched_keywords && atsAnalysis.matched_keywords.length > 0) {
      const matchedDiv = document.createElement("div")
      matchedDiv.className = "keyword-section"
      matchedDiv.innerHTML = `
                <h4><i class="fas fa-check-circle" style="color: var(--success-color);"></i> Matched Keywords</h4>
                <div class="keyword-tags">
                    ${atsAnalysis.matched_keywords
                      .map((keyword) => `<span class="keyword-tag matched">${keyword}</span>`)
                      .join("")}
                </div>
            `
      keywordsContent.appendChild(matchedDiv)
    }

    // Missing keywords by category
    if (atsAnalysis.category_scores) {
      Object.entries(atsAnalysis.category_scores).forEach(([category, data]) => {
        if (data.missing && data.missing.length > 0) {
          const missingDiv = document.createElement("div")
          missingDiv.className = "keyword-section"
          missingDiv.innerHTML = `
                        <h4><i class="fas fa-exclamation-circle" style="color: var(--warning-color);"></i> Missing ${category.charAt(0).toUpperCase() + category.slice(1)} Keywords</h4>
                        <div class="keyword-tags">
                            ${data.missing
                              .map((keyword) => `<span class="keyword-tag missing">${keyword}</span>`)
                              .join("")}
                        </div>
                    `
          keywordsContent.appendChild(missingDiv)
        }
      })
    }
  }
}

function updateRecommendationsTab(recommendations) {
  const recommendationsContent = document.querySelector(".recommendations-content")
  if (recommendationsContent) {
    recommendationsContent.innerHTML = ""
    recommendations.forEach((recommendation) => {
      const recommendationDiv = document.createElement("div")
      recommendationDiv.className = "recommendation-item"
      recommendationDiv.innerHTML = `
                <i class="fas fa-lightbulb"></i>
                <span>${recommendation}</span>
            `
      recommendationsContent.appendChild(recommendationDiv)
    })
  }
}

function initializeActionButtons() {
  const downloadBtn = document.getElementById("downloadBtn")
  const copyBtn = document.getElementById("copyBtn")

  if (downloadBtn) {
    downloadBtn.addEventListener("click", handleDownload)
  }

  if (copyBtn) {
    copyBtn.addEventListener("click", handleCopyImprovements)
  }
}

function handleDownload() {
  if (!window.currentResults) {
    showNotification("No analysis results to download", "error")
    return
  }

  const results = window.currentResults
  const content = generateDownloadContent(results)

  const blob = new Blob([content], { type: "text/plain" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "resume_analysis_report.txt"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  showNotification("Report downloaded successfully!", "success")
}

function generateDownloadContent(results) {
  const { ats_analysis, ai_suggestions, resume_text } = results

  let content = `CAREER COSMOS - ATS RESUME ANALYSIS REPORT
${"=".repeat(50)}

OVERALL ATS SCORE: ${Math.round(ats_analysis.overall_score)}/100

CATEGORY BREAKDOWN:
`

  Object.entries(ats_analysis.category_scores).forEach(([category, data]) => {
    content += `- ${category.toUpperCase()}: ${data.score}%\n`
  })

  content += `\nMATCHED KEYWORDS (${ats_analysis.matched_count}/${ats_analysis.total_job_keywords}):
${ats_analysis.matched_keywords.join(", ")}

HIGHLIGHTED CORRECTIONS:
`

  ai_suggestions.highlighted_corrections.forEach((correction, index) => {
    content += `${index + 1}. ${correction}\n`
  })

  content += `\nREWRITTEN SECTIONS:
`

  Object.entries(ai_suggestions.rewritten_sections).forEach(([section, text]) => {
    content += `\n${section.toUpperCase()}:\n${text}\n`
  })

  content += `\nKEYWORD OPTIMIZATION:
`

  ai_suggestions.keyword_optimization.forEach((tip, index) => {
    content += `${index + 1}. ${tip}\n`
  })

  content += `\nOVERALL RECOMMENDATIONS:
`

  ai_suggestions.overall_recommendations.forEach((rec, index) => {
    content += `${index + 1}. ${rec}\n`
  })

  content += `\n${"=".repeat(50)}
Generated by Career Cosmos ATS Enhancement Tool
${new Date().toLocaleString()}`

  return content
}

function handleCopyImprovements() {
  if (!window.currentResults) {
    showNotification("No analysis results to copy", "error")
    return
  }

  const improvements = generateImprovementsText(window.currentResults.ai_suggestions)
  copyToClipboard(improvements)
}

function generateImprovementsText(aiSuggestions) {
  let text = "RESUME IMPROVEMENTS:\n\n"

  text += "CORRECTIONS:\n"
  aiSuggestions.highlighted_corrections.forEach((correction, index) => {
    text += `${index + 1}. ${correction}\n`
  })

  text += "\nREWRITTEN SECTIONS:\n"
  Object.entries(aiSuggestions.rewritten_sections).forEach(([section, content]) => {
    text += `\n${section.toUpperCase()}:\n${content}\n`
  })

  return text
}

// Add CSS for keyword tags
const keywordStyles = document.createElement("style")
keywordStyles.textContent = `
    .keyword-section {
        margin-bottom: 2rem;
    }
    
    .keyword-section h4 {
        color: var(--text-primary);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .keyword-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .keyword-tag {
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .keyword-tag.matched {
        background: var(--success-color);
        color: var(--secondary-color);
    }
    
    .keyword-tag.missing {
        background: var(--warning-color);
        color: white;
    }
    
    .copy-section-btn {
        background: var(--primary-color);
        color: var(--secondary-color);
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
        font-size: 0.9rem;
        margin-top: 1rem;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .copy-section-btn:hover {
        opacity: 0.8;
    }
`
document.head.appendChild(keywordStyles)

// Declare functions before using them
function clearAutoSave(formId) {
  // Implementation for clearAutoSave
  console.log(`Auto-save cleared for form ${formId}`)
}

function showNotification(message, type) {
  // Implementation for showNotification
  console.log(`Notification: ${message} (Type: ${type})`)
}

function copyToClipboard(text) {
  // Implementation for copyToClipboard
  console.log(`Text copied to clipboard: ${text}`)
}
