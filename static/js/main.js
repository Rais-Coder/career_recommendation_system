class CareerApp {
    constructor() {
        this.currentUser = null;
        this.recommendations = [];
        this.skills = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeTooltips();
        
        // Only load user data on pages that require it
        if (this.shouldLoadUserData()) {
            this.loadUserData();
        }
    }

    shouldLoadUserData() {
        const path = window.location.pathname;
        const protectedPages = [
            '/dashboard',
            '/get_recommendations'
        ];
        return protectedPages.includes(path);
    }

    setupEventListeners() {
        // Navigation menu toggle for mobile
        const navToggle = document.getElementById('navToggle');
        const navMenu = document.querySelector('.nav-menu');
        
        if (navToggle && navMenu) {
            navToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
            });
        }

        // Smooth scrolling for anchor links
        document.addEventListener('click', (e) => {
            if (e.target.matches('a[href^="#"]')) {
                e.preventDefault();
                const target = document.querySelector(e.target.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });

        // Resume upload form
        const resumeForm = document.getElementById('resumeUploadForm');
        if (resumeForm) {
            this.setupResumeUpload();
        }
    
        // Search and filter functionality
        this.setupSearchFilters();
        
        // Interactive elements
        this.setupInteractiveElements();

        // Assessment form submission
        this.setupAssessmentForm();
    }

    setupAssessmentForm() {
        const assessmentForm = document.getElementById('careerAssessment');
        if (assessmentForm) {
            // Update slider values in real-time
            assessmentForm.querySelectorAll('input[type="range"]').forEach(slider => {
                const output = slider.nextElementSibling;
                if (output && output.classList.contains('slider-value')) {
                    // Set initial value
                    output.textContent = slider.value;
                    
                    slider.addEventListener('input', (e) => {
                        output.textContent = e.target.value;
                    });
                }
            });

            // Handle form submission
            assessmentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitAssessment(assessmentForm);
            });
        }
    }

    async submitAssessment(form) {
        try {
            this.showLoading('Submitting assessment...');
            
            const formData = new FormData(form);
            
            // Add checkbox values properly
            const interests = form.querySelectorAll('input[name="interests"]:checked');
            interests.forEach(checkbox => {
                formData.append('interests', checkbox.value);
            });

            const response = await fetch('/submit_assessment', {
                method: 'POST',
                body: formData
            });

            this.hideLoading();

            if (response.ok) {
                window.location.href = '/upload_resume';
            } else {
                this.showNotification('Assessment submission failed', 'error');
            }
        } catch (error) {
            this.hideLoading();
            this.showNotification('Network error: ' + error.message, 'error');
        }
    }

    setupResumeUpload() {
        const resumeForm = document.getElementById('resumeUploadForm');
        const fileInput = document.getElementById('resume_file');
        const uploadStatus = document.querySelector('.upload-status');
        const skillsList = document.getElementById('extracted-skills-list');

        resumeForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(resumeForm);
            
            try {
                uploadStatus.classList.remove('hidden');
                this.showLoading('Uploading resume...');

                const response = await fetch('/process_resume', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                this.hideLoading();
                uploadStatus.classList.add('hidden');

                if (result.success) {
                    this.showNotification('Resume uploaded successfully! Generating recommendations...', 'success');
                    skillsList.innerHTML = '';
                    result.skills.forEach(skill => {
                        const li = document.createElement('li');
                        li.textContent = skill;
                        skillsList.appendChild(li);
                    });
                    document.querySelector('.extracted-skills').classList.remove('hidden');
                    
                    // Redirect to recommendations after successful processing
                    setTimeout(() => {
                        window.location.href = '/get_recommendations';
                    }, 2000);
                } else {
                    this.showNotification('Resume upload failed: ' + result.error, 'error');
                }
            } catch (error) {
                this.hideLoading();
                uploadStatus.classList.add('hidden');
                this.showNotification('Network error: ' + error.message, 'error');
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                uploadStatus.classList.remove('hidden');
            }
        });
    }

    setupSearchFilters() {
        const industryFilter = document.getElementById('industry_filter');
        const salaryFilter = document.getElementById('salary_filter');
        const matchFilter = document.getElementById('match_filter');

        if (industryFilter && salaryFilter && matchFilter) {
            [industryFilter, salaryFilter, matchFilter].forEach(filter => {
                filter.addEventListener('change', this.applyFilters.bind(this));
            });
        }
    }

    applyFilters() {
        const filters = {
            industry: document.getElementById('industry_filter')?.value || '',
            minSalary: parseInt(document.getElementById('salary_filter')?.value) || 0,
            minMatch: parseFloat(document.getElementById('match_filter')?.value) || 0
        };

        const cards = document.querySelectorAll('.recommendation-card');
        
        cards.forEach(card => {
            const cardIndustry = card.dataset.industry;
            const cardSalary = parseInt(card.dataset.salary);
            const cardMatch = parseFloat(card.dataset.match);
            
            const showCard = this.matchesFilters(cardIndustry, cardSalary, cardMatch, filters);
            
            card.style.display = showCard ? 'block' : 'none';
            
            if (showCard) {
                card.classList.add('fade-in-up');
            }
        });
    }

    matchesFilters(industry, salary, match, filters) {
        const industryMatch = !filters.industry || industry === filters.industry;
        const salaryMatch = !filters.minSalary || salary >= filters.minSalary;
        const matchScoreMatch = !filters.minMatch || match >= filters.minMatch;
        
        return industryMatch && salaryMatch && matchScoreMatch;
    }

    setupInteractiveElements() {
        // Skill level sliders
        document.querySelectorAll('input[type="range"]').forEach(slider => {
            const output = slider.nextElementSibling;
            if (output && output.classList.contains('slider-value')) {
                slider.addEventListener('input', (e) => {
                    output.textContent = e.target.value;
                });
            }
        });

        // Explore career buttons
        document.querySelectorAll('.explore-career').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const careerId = e.target.dataset.careerId;
                if (careerId) {
                    this.exploreCareer(careerId);
                }
            });
        });
    }

    async exploreCareer(careerId) {
        try {
            this.showLoading('Loading career details...');
            
            const response = await fetch(`/api/career_details/${careerId}`);
            const careerData = await response.json();
            
            this.hideLoading();
            
            if (careerData.error) {
                this.showNotification('Failed to load career details', 'error');
                return;
            }
            
            this.showCareerModal(careerData);
        } catch (error) {
            this.hideLoading();
            this.showNotification('Network error: ' + error.message, 'error');
        }
    }

    showCareerModal(careerData) {
        const modal = this.createModal('career-details-modal', 'Career Details');
        
        const content = `
            <div class="career-details">
                <h3>${careerData.career_title}</h3>
                <p><strong>Industry:</strong> ${careerData.industry}</p>
                <p><strong>Description:</strong> ${careerData.description}</p>
                <p><strong>Salary Range:</strong> $${careerData.avg_salary_min.toLocaleString()} - $${careerData.avg_salary_max.toLocaleString()}</p>
                <p><strong>Growth Rate:</strong> ${(careerData.growth_rate * 100).toFixed(0)}% annually</p>
                <p><strong>Education Required:</strong> ${careerData.education_required}</p>
                <p><strong>Experience Required:</strong> ${careerData.experience_required}</p>
                <p><strong>Remote Friendly:</strong> ${careerData.remote_friendly ? 'Yes' : 'No'}</p>
                <div class="skills-required">
                    <h4>Required Skills:</h4>
                    <ul>
                        ${careerData.required_skills.map(skill => `<li>${skill}</li>`).join('')}
                    </ul>
                </div>
                <button class="btn btn-primary close-modal">Close</button>
            </div>
        `;
        
        modal.innerHTML = content;
        document.body.appendChild(modal);

        // Add close button functionality
        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.remove();
        });

        // Close modal on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    createModal(id, title) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = id;
        modal.innerHTML = `
            <div class="modal-content">
                <h2>${title}</h2>
                <span class="modal-close">&times;</span>
            </div>
        `;
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });
        return modal;
    }

    initializeTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', () => {
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = element.dataset.tooltip;
                document.body.appendChild(tooltip);

                const rect = element.getBoundingClientRect();
                tooltip.style.top = `${rect.top + window.scrollY - tooltip.offsetHeight - 5}px`;
                tooltip.style.left = `${rect.left + window.scrollX + (rect.width - tooltip.offsetWidth) / 2}px`;

                element.addEventListener('mouseleave', () => {
                    tooltip.remove();
                }, { once: true });
            });
        });
    }

    async loadUserData() {
        try {
            const response = await fetch('/api/user_data');
            
            if (response.status === 401) {
                // User not logged in, redirect to home
                if (this.shouldLoadUserData()) {
                    window.location.href = '/';
                }
                return;
            }
            
            const data = await response.json();
            if (data.success) {
                this.currentUser = data.user;
                this.skills = data.skills;
                this.recommendations = data.recommendations;
                this.updateDashboard();
            }
        } catch (error) {
            console.error('Failed to load user data:', error);
        }
    }

    updateDashboard() {
        const skillsList = document.querySelector('.skills-list');
        const recommendationsList = document.querySelector('.recommendations-list');
        const userStats = document.querySelector('.dashboard-stats');

        if (userStats && this.currentUser) {
            const statCards = userStats.querySelectorAll('.stat-card');
            if (statCards[0]) statCards[0].querySelector('.stat-number').textContent = this.skills.length;
            if (statCards[1]) statCards[1].querySelector('.stat-number').textContent = this.recommendations.length;
            if (statCards[2]) statCards[2].querySelector('.stat-number').textContent = this.currentUser.education_level || 'N/A';
            if (statCards[3]) statCards[3].querySelector('.stat-number').textContent = this.currentUser.years_experience || 0;
        }

        if (skillsList) {
            skillsList.innerHTML = this.skills.slice(0, 10).map(skill => `
                <div class="skill-card">
                    <div>
                        <strong>${skill.skill_name}</strong>
                        <p>${skill.category}</p>
                    </div>
                    <div class="skill-proficiency">
                        <div class="progress-bar"><div style="width: ${skill.proficiency_level * 20}%"></div></div>
                        <span>${skill.proficiency_level}/5</span>
                    </div>
                </div>
            `).join('');
        }

        if (recommendationsList) {
            recommendationsList.innerHTML = this.recommendations.slice(0, 3).map(rec => `
                <div class="recommendation-card">
                    <div class="rec-title-section">
                        <h3>${rec.career_title}</h3>
                        <span class="match-score">${Math.round(rec.match_score * 100)}% Match</span>
                    </div>
                    <p>${rec.industry}</p>
                    <p>$${rec.avg_salary_min.toLocaleString()} - $${rec.avg_salary_max.toLocaleString()}</p>
                </div>
            `).join('');
        }
    }

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('Text copied to clipboard!', 'success');
        }).catch(() => {
            this.showNotification('Failed to copy text', 'error');
        });
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 500);
        }, 3000);
    }

    showLoading(message) {
        const loading = document.createElement('div');
        loading.className = 'loading-overlay';
        loading.innerHTML = `<div class="loading-spinner"></div><p>${message}</p>`;
        document.body.appendChild(loading);
    }

    hideLoading() {
        const loading = document.querySelector('.loading-overlay');
        if (loading) {
            loading.remove();
        }
    }
}