/**
 * Financial Dashboard JS
 * Improved version with better organization, performance, and accessibility
 */

// Use an IIFE to avoid polluting the global scope
(function() {
    // Cache DOM references for frequently accessed elements
    const DOM = {
      // Counters
      incomeCounter: null,
      expenseCounter: null,
      balanceCounter: null,
      balanceTrend: null,
      
      // Charts
      categoryChart: null,
      trendChart: null,
      
      // Transaction elements
      transactionList: null,
      transactionForm: null,
      transactionModal: null,
      
      // Filters
      dateFilter: null,
      categoryFilter: null,
      activeFiltersContainer: null,
      
      // FAB elements
      fabButton: null,
      fabOptions: null,
      
      // Message system
      messageForm: null,
      messageInput: null,
      messageList: null,
      
      // Initialize all references
      init() {
        this.incomeCounter = document.getElementById('income-counter');
        this.expenseCounter = document.getElementById('expense-counter');
        this.balanceCounter = document.getElementById('balance-counter');
        this.balanceTrend = document.getElementById('balance-trend');
        
        this.categoryChart = document.getElementById('categoryChart');
        this.trendChart = document.getElementById('trendChart');
        
        this.transactionList = document.getElementById('transaction-list');
        this.transactionForm = document.getElementById('add-transaction-form');
        this.transactionModal = document.getElementById('add-transaction-modal');
        
        this.dateFilter = document.getElementById('date-filter');
        this.categoryFilter = document.getElementById('category-filter');
        this.activeFiltersContainer = document.getElementById('activeFilters');
        
        this.fabButton = document.getElementById('fabButton');
        this.fabOptions = document.getElementById('fabOptions');
        
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
        this.messageList = document.getElementById('message-list');
      }
    };
    
    // Theme manager
    const ThemeManager = {
      // Check for user's preferred color scheme
      init() {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('dashboard-theme');
        
        if (savedTheme) {
          this.setTheme(savedTheme);
        } else if (prefersDark) {
          this.setTheme('dark');
        }
        
        // Add theme toggle button event listener
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
          themeToggle.addEventListener('click', () => {
            const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
            this.setTheme(currentTheme === 'dark' ? 'light' : 'dark');
          });
        }
      },
      
      setTheme(theme) {
        if (theme === 'dark') {
          document.body.classList.add('dark-theme');
          localStorage.setItem('dashboard-theme', 'dark');
        } else {
          document.body.classList.remove('dark-theme');
          localStorage.setItem('dashboard-theme', 'light');
        }
        
        // Update theme toggle icon if it exists
        const themeIcon = document.querySelector('#theme-toggle i');
        if (themeIcon) {
          themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
      }
    };
    
    // Animation manager with performance optimizations
    const AnimationManager = {
      // Animate counters with better performance
      animateCounter(element, targetValue, duration = 1000) {
        if (!element) return Promise.resolve();
        
        return new Promise(resolve => {
          // Parse the target value
          const value = parseFloat(targetValue.toString().replace('₹', '').replace(/,/g, ''));
          const startTime = performance.now();
          const startValue = 0;
          
          const updateCounter = (timestamp) => {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Optimized easing function
            const easeProgress = 1 - Math.pow(1 - progress, 2);
            const currentValue = Math.floor(startValue + (easeProgress * (value - startValue)));
            
            element.textContent = '₹' + currentValue.toLocaleString();
            
            if (progress < 1) {
              requestAnimationFrame(updateCounter);
            } else {
              resolve();
            }
          };
          
          requestAnimationFrame(updateCounter);
        });
      },
      
      // Fade in element
      fadeIn(element, duration = 300) {
        if (!element) return;
        
        element.style.opacity = '0';
        element.style.display = 'block';
        
        const startTime = performance.now();
        
        const animate = (timestamp) => {
          const elapsed = timestamp - startTime;
          const progress = Math.min(elapsed / duration, 1);
          
          element.style.opacity = progress.toString();
          
          if (progress < 1) {
            requestAnimationFrame(animate);
          }
        };
        
        requestAnimationFrame(animate);
      },
      
      // Fade out element
      fadeOut(element, duration = 300) {
        if (!element) return Promise.resolve();
        
        return new Promise(resolve => {
          const startOpacity = parseFloat(getComputedStyle(element).opacity);
          const startTime = performance.now();
          
          const animate = (timestamp) => {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = (startOpacity * (1 - progress)).toString();
            
            if (progress < 1) {
              requestAnimationFrame(animate);
            } else {
              element.style.display = 'none';
              resolve();
            }
          };
          
          requestAnimationFrame(animate);
        });
      }
    };
    
    // Chart manager with responsive options
    const ChartManager = {
      charts: {
        category: null,
        trend: null
      },
      
      init() {
        if (typeof Chart === 'undefined') {
          console.error('Chart.js is not loaded');
          return;
        }
        
        this.initCategoryChart();
        this.setupListeners();
      },
      
      // Initialize the expense category chart
      initCategoryChart() {
        if (!DOM.categoryChart) return;
        
        const ctx = DOM.categoryChart.getContext('2d');
        
        // Category data (fetch this dynamically in production)
        const categories = ['Housing', 'Food', 'Transport', 'Entertainment', 'Utilities', 'Others'];
        const values = [20000, 15000, 8000, 5000, 4000, 3000];
        const backgroundColors = [
          'rgba(255, 99, 132, 0.7)',
          'rgba(54, 162, 235, 0.7)',
          'rgba(255, 206, 86, 0.7)',
          'rgba(75, 192, 192, 0.7)',
          'rgba(153, 102, 255, 0.7)',
          'rgba(255, 159, 64, 0.7)'
        ];
        const borderColors = backgroundColors.map(color => color.replace('0.7', '1'));
        
        // Responsive font sizes
        Chart.defaults.font.size = window.innerWidth < 768 ? 12 : 14;
        
        this.charts.category = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: categories,
            datasets: [{
              label: 'Expenses by Category',
              data: values,
              backgroundColor: backgroundColors,
              borderColor: borderColors,
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: context => '₹' + context.raw.toLocaleString()
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  callback: value => '₹' + value.toLocaleString()
                }
              }
            },
            animation: {
              duration: 1500,
              easing: 'easeOutQuart'
            }
          }
        });
      },
      
      // Initialize trend chart (using existing code with improvements)
      initTrendChart() {
        try {
          var ctx = document.getElementById('trendChart').getContext('2d');
          
          var chartLabels = JSON.parse(document.getElementById('chart-labels')?.textContent || '[]');
          var chartIncome = JSON.parse(document.getElementById('chart-income')?.textContent || '[]');
          var chartExpenses = JSON.parse(document.getElementById('chart-expenses')?.textContent || '[]');
          
          this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
              labels: chartLabels,
              datasets: [
                {
                  label: 'Income',
                  data: chartIncome,
                  borderColor: '#28a745',
                  backgroundColor: 'rgba(40, 167, 69, 0.1)',
                  borderWidth: 2,
                  tension: 0.1,
                  fill: true
                },
                {
                  label: 'Expenses',
                  data: chartExpenses,
                  borderColor: '#dc3545',
                  backgroundColor: 'rgba(220, 53, 69, 0.1)',
                  borderWidth: 2,
                  tension: 0.1,
                  fill: true
                }
              ]
            },
            options: {
              responsive: true,
              scales: {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: 'Amount'
                  }
                },
                x: {
                  title: {
                    display: true,
                    text: 'Month'
                  }
                }
              },
              plugins: {
                legend: {
                  position: 'top',
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      var label = context.dataset.label || '';
                      if (label) {
                        label += ': ';
                      }
                      if (context.parsed.y !== null) {
                        label += new Intl.NumberFormat('en-IN', { 
                          style: 'currency', 
                          currency: 'INR',
                          maximumFractionDigits: 0
                        }).format(context.parsed.y);
                      }
                      return label;
                    }
                  }
                }
              },
              animation: {
                duration: 1000
              }
            }
          });
        } catch (error) {
          console.error('Error initializing trend chart:', error);
        }
      },
      
      // Update chart with new data
      updateCategoryChart(newData) {
        if (!this.charts.category) return;
        
        this.charts.category.data.datasets[0].data = newData;
        this.charts.category.update();
      },
      
      // Handle window resize for chart responsiveness
      setupListeners() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
          clearTimeout(resizeTimeout);
          resizeTimeout = setTimeout(() => {
            Chart.defaults.font.size = window.innerWidth < 768 ? 12 : 14;
            
            if (this.charts.category) {
              this.charts.category.resize();
            }
            
            if (this.charts.trend) {
              this.charts.trend.resize();
            }
          }, 250);
        });
      }
    };
    
    // Transaction Manager
    const TransactionManager = {
      transactions: [],
      
      init() {
        this.registerEventListeners();
        this.loadTransactions();
      },
      
      registerEventListeners() {
        // Transaction form submission
        if (DOM.transactionForm) {
          DOM.transactionForm.addEventListener('submit', this.handleTransactionSubmit.bind(this));
        }
        
        // Add event delegation for transaction list actions
        if (DOM.transactionList) {
          DOM.transactionList.addEventListener('click', this.handleTransactionClick.bind(this));
        }
      },
      
      handleTransactionSubmit(e) {
        e.preventDefault();
        
        try {
          // Get form data
          const form = e.target;
          const formData = new FormData(form);
          
          const transactionData = {
            id: Date.now(), // Use timestamp as unique ID
            type: formData.get('transaction-type'),
            category: formData.get('transaction-category'),
            amount: parseFloat(formData.get('transaction-amount')),
            description: formData.get('transaction-description'),
            date: formData.get('transaction-date')
          };
          
          // Validate data
          if (!transactionData.type || !transactionData.category || 
              isNaN(transactionData.amount) || !transactionData.date) {
            NotificationManager.showNotification('Please fill all required fields', 'warning');
            return;
          }
          
          // Add transaction
          this.addTransaction(transactionData);
          
          // Close modal
          const modalElement = DOM.transactionModal;
          if (modalElement) {
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
              modalInstance.hide();
            }
          }
          
          // Show success message
          NotificationManager.showNotification('Transaction added successfully!', 'success');
          
          // Reset form
          form.reset();
        } catch (error) {
          console.error('Error submitting transaction:', error);
          NotificationManager.showNotification('Failed to add transaction', 'error');
        }
      },
      
      handleTransactionClick(e) {
        // Handle edit or delete actions via delegation
        const editBtn = e.target.closest('.edit-transaction');
        const deleteBtn = e.target.closest('.delete-transaction');
        
        if (editBtn) {
          const transactionId = editBtn.dataset.id;
          this.editTransaction(transactionId);
        } else if (deleteBtn) {
          const transactionId = deleteBtn.dataset.id;
          if (confirm('Are you sure you want to delete this transaction?')) {
            this.deleteTransaction(transactionId);
          }
        }
      },
      
      loadTransactions() {
        // Use a try-catch in case localStorage is unavailable
        try {
          const savedTransactions = localStorage.getItem('financial-dashboard-transactions');
          if (savedTransactions) {
            this.transactions = JSON.parse(savedTransactions);
          } else {
            // Load sample data if no transactions exist
            this.transactions = this.getSampleTransactions();
            this.saveTransactions();
          }
          
          this.renderTransactions();
        } catch (error) {
          console.error('Error loading transactions:', error);
          this.transactions = this.getSampleTransactions();
          this.renderTransactions();
        }
      },
      
      saveTransactions() {
        try {
          localStorage.setItem('financial-dashboard-transactions', JSON.stringify(this.transactions));
        } catch (error) {
          console.error('Error saving transactions:', error);
        }
      },
      
      addTransaction(transaction) {
        this.transactions.unshift(transaction);
        this.saveTransactions();
        this.renderTransactions();
        DashboardManager.updateDashboardSummary();
      },
      
      editTransaction(id) {
        const transaction = this.transactions.find(t => t.id.toString() === id.toString());
        if (!transaction) return;
        
        // Populate form with transaction data
        if (DOM.transactionForm) {
          const form = DOM.transactionForm;
          form.elements['transaction-type'].value = transaction.type;
          form.elements['transaction-category'].value = transaction.category;
          form.elements['transaction-amount'].value = transaction.amount;
          form.elements['transaction-description'].value = transaction.description;
          form.elements['transaction-date'].value = transaction.date;
          
          // Add update flag and ID
          form.dataset.editMode = 'true';
          form.dataset.editId = id;
          
          // Show modal
          if (DOM.transactionModal) {
            const modalInstance = new bootstrap.Modal(DOM.transactionModal);
            modalInstance.show();
          }
        }
      },
      
      deleteTransaction(id) {
        const index = this.transactions.findIndex(t => t.id.toString() === id.toString());
        if (index === -1) return;
        
        this.transactions.splice(index, 1);
        this.saveTransactions();
        this.renderTransactions();
        DashboardManager.updateDashboardSummary();
        
        NotificationManager.showNotification('Transaction deleted successfully', 'success');
      },
      
      renderTransactions(filterCategory = 'all') {
        if (!DOM.transactionList) return;
        
        // Clear existing list
        DOM.transactionList.innerHTML = '';
        
        // Filter transactions
        const filteredTransactions = filterCategory === 'all' ? 
          this.transactions : 
          this.transactions.filter(t => t.category === filterCategory);
        
        // Handle empty state
        if (filteredTransactions.length === 0) {
          DOM.transactionList.innerHTML = `
            <div class="text-center py-4">
              <div class="text-muted mb-2">No transactions found</div>
              <button class="btn btn-sm btn-primary" id="add-first-transaction">
                <i class="fas fa-plus-circle me-1"></i> Add your first transaction
              </button>
            </div>
          `;
          
          const addBtn = document.getElementById('add-first-transaction');
          if (addBtn) {
            addBtn.addEventListener('click', () => {
              if (DOM.transactionModal) {
                const modalInstance = new bootstrap.Modal(DOM.transactionModal);
                modalInstance.show();
              }
            });
          }
          
          return;
        }
        
        // Create and append fragment for better performance
        const fragment = document.createDocumentFragment();
        
        filteredTransactions.forEach(transaction => {
          const listItem = this.createTransactionItem(transaction);
          fragment.appendChild(listItem);
        });
        
        DOM.transactionList.appendChild(fragment);
      },
      
      createTransactionItem(transaction) {
        const listItem = document.createElement('div');
        listItem.className = 'transaction-item p-3 border-bottom animate__animated animate__fadeIn';
        listItem.dataset.id = transaction.id;
        
        const amountClass = transaction.type === 'income' ? 'text-success' : 'text-danger';
        const amountPrefix = transaction.type === 'income' ? '+' : '-';
        const formattedDate = this.formatDate(transaction.date);
        const categoryBadge = this.getCategoryBadge(transaction.category);
        
        listItem.innerHTML = `
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h6 class="mb-1">${transaction.description}</h6>
              <div class="d-flex align-items-center">
                <small class="text-muted me-2">${formattedDate}</small>
                ${categoryBadge}
              </div>
            </div>
            <div class="d-flex align-items-center">
              <div class="fw-bold ${amountClass} me-3">
                ${amountPrefix}₹${transaction.amount.toLocaleString()}
              </div>
              <div class="btn-group">
                <button class="btn btn-sm btn-outline-secondary edit-transaction" data-id="${transaction.id}" aria-label="Edit transaction">
                  <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger delete-transaction" data-id="${transaction.id}" aria-label="Delete transaction">
                  <i class="fas fa-trash-alt"></i>
                </button>
              </div>
            </div>
          </div>
        `;
        
        return listItem;
      },
      
      getCategoryBadge(category) {
        const categories = {
          'housing': { color: 'primary', icon: 'home' },
          'food': { color: 'success', icon: 'utensils' },
          'transport': { color: 'info', icon: 'car' },
          'entertainment': { color: 'warning', icon: 'film' },
          'utilities': { color: 'secondary', icon: 'bolt' },
          'salary': { color: 'success', icon: 'money-bill-wave' },
          'freelance': { color: 'info', icon: 'laptop' },
          'investment': { color: 'primary', icon: 'chart-line' }
        };
        
        const categoryInfo = categories[category] || { color: 'dark', icon: 'tag' };
        
        return `
          <span class="badge bg-${categoryInfo.color}-subtle text-${categoryInfo.color} rounded-pill">
            <i class="fas fa-${categoryInfo.icon} me-1"></i>${this.capitalize(category)}
          </span>
        `;
      },
      
      getSampleTransactions() {
        return [
          { id: 1, date: '2025-02-18', description: 'Salary', amount: 58000, type: 'income', category: 'salary' },
          { id: 2, date: '2025-02-17', description: 'Rent Payment', amount: 20000, type: 'expense', category: 'housing' },
          { id: 3, date: '2025-02-15', description: 'Grocery Shopping', amount: 3500, type: 'expense', category: 'food' },
          { id: 4, date: '2025-02-14', description: 'Freelance Work', amount: 15000, type: 'income', category: 'freelance' },
          { id: 5, date: '2025-02-12', description: 'Electricity Bill', amount: 2800, type: 'expense', category: 'utilities' },
          { id: 6, date: '2025-02-10', description: 'Restaurant Dinner', amount: 2200, type: 'expense', category: 'food' },
          { id: 7, date: '2025-02-08', description: 'Fuel', amount: 1500, type: 'expense', category: 'transport' },
          { id: 8, date: '2025-02-05', description: 'Movie Tickets', amount: 800, type: 'expense', category: 'entertainment' }
        ];
      },
      
      formatDate(dateString) {
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(dateString).toLocaleDateString(undefined, options);
      },
      
      capitalize(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
      },
      
      getCategoryTotals() {
        const categories = {};
        
        this.transactions.forEach(transaction => {
          if (transaction.type === 'expense') {
            if (!categories[transaction.category]) {
              categories[transaction.category] = 0;
            }
            categories[transaction.category] += transaction.amount;
          }
        });
        
        return categories;
      },
      
      getTotalIncome() {
        return this.transactions
          .filter(t => t.type === 'income')
          .reduce((sum, t) => sum + t.amount, 0);
      },
      
      getTotalExpense() {
        return this.transactions
          .filter(t => t.type === 'expense')
          .reduce((sum, t) => sum + t.amount, 0);
      }
    };
    
    // Filter Manager
    const FilterManager = {
      activeFilters: {
        date: null,
        category: null,
        search: null
      },
      
      init() {
        this.setupFilterListeners();
        this.updateActiveFiltersDisplay();
      },
      
      setupFilterListeners() {
        // Date filter
        if (DOM.dateFilter) {
          DOM.dateFilter.addEventListener('change', () => {
            this.activeFilters.date = DOM.dateFilter.value;
            this.applyFilters();
          });
        }
        
        // Category filter
        if (DOM.categoryFilter) {
          DOM.categoryFilter.addEventListener('change', () => {
            this.activeFilters.category = DOM.categoryFilter.value;
            this.applyFilters();
          });
        }
        
        // Search filter
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
          // Debounce search to improve performance
          let searchTimeout;
          searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
              this.activeFilters.search = searchInput.value.trim();
              this.applyFilters();
            }, 300);
          });
        }
        
        // Clear all filters button
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
          clearFiltersBtn.addEventListener('click', this.clearAllFilters.bind(this));
        }
      },
      
      applyFilters() {
        // Show loading state
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
          loadingIndicator.classList.remove('d-none');
        }
        
        // Apply filters to transaction list
        TransactionManager.renderTransactions(this.activeFilters.category);
        
        // Update dashboard data based on filters
        DashboardManager.updateDashboardData(this.activeFilters.date, this.activeFilters.category);
        
        // Update active filters display
        this.updateActiveFiltersDisplay();
        
        // Hide loading after a short delay
        setTimeout(() => {
          if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
          }
        }, 400);
      },
      
      updateActiveFiltersDisplay() {
        if (!DOM.activeFiltersContainer) return;
        
        // Clear current filters
        DOM.activeFiltersContainer.innerHTML = '';
        
        let hasActiveFilters = false;
        
        // Add filters if they exist
        if (this.activeFilters.date) {
          this.createFilterPill('Date', this.formatFilterValue(this.activeFilters.date), 'date');
          hasActiveFilters = true;
        }
        
        if (this.activeFilters.category && this.activeFilters.category !== 'all') {
          this.createFilterPill('Category', this.formatFilterValue(this.activeFilters.category), 'category');
          hasActiveFilters = true;
        }
        
        if (this.activeFilters.search) {
          this.createFilterPill('Search', this.activeFilters.search, 'search');
          hasActiveFilters = true;
        }
        
        // Show heading and clear button if we have filters
        if (hasActiveFilters) {
          DOM.activeFiltersContainer.prepend(this.createElement('span', 'Active filters: ', 'me-2 fw-bold'));
          
          // Add clear all button if not already present
          if (!document.getElementById('clear-filters')) {
            const clearBtn = this.createElement('button', 'Clear All', 'btn btn-sm btn-outline-secondary ms-2');
            clearBtn.id = 'clear-filters';
            clearBtn.addEventListener('click', this.clearAllFilters.bind(this));
            DOM.activeFiltersContainer.appendChild(clearBtn);
          }
        }
      },
      
      createFilterPill(label, value, param) {
        if (!DOM.activeFiltersContainer) return;
        
        const pill = this.createElement('span', '', 'badge bg-primary rounded-pill me-2 mb-2 p-2');
        
        pill.innerHTML = `${label}: ${value} <i class="fas fa-times-circle ms-1" style="cursor:pointer;" aria-label="Remove ${label} filter"></i>`;
        
        // Add click event to remove this filter
        pill.querySelector('i').addEventListener('click', () => {
          this.activeFilters[param] = null;
          
          // Reset form control value
          if (param === 'date' && DOM.dateFilter) {
            DOM.dateFilter.value = '';
          } else if (param === 'category' && DOM.categoryFilter) {
            DOM.categoryFilter.value = 'all';
          } else if (param === 'search') {
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) searchInput.value = '';
          }
          
          this.applyFilters();
        });
        
        DOM.activeFiltersContainer.appendChild(pill);
      },
      
      clearAllFilters() {
        this.activeFilters = {
          date: null,
          category: null,
          search: null
        };
        
        // Reset form controls
        if (DOM.dateFilter) DOM.dateFilter.value = '';
        if (DOM.categoryFilter) DOM.categoryFilter.value = 'all';
        
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) searchInput.value = '';
        
        this.applyFilters();
      },
    }
    
      
    //   formatFilterValue(value) {
    //     // Make filter values more readable
    //     switch(value) {
    //       case 'this-month':
    //         return 'This Month';
    //       case 'last-month':
    //         return 'Last Month';
    //       case 'last-3-months':
    //         return 'Last 3 Months';
    //       default:
    //         return value.charAt(0).toUpperCase() + value.slice(1);
    //     }
    //   }      
    //   createElement(tag, text, classes) {
    //     const el = document.createElement(tag)}}