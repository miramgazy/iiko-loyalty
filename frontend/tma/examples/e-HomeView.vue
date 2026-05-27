<template>
  <div class="home-view">
    <!-- ══ SUCCESS ══ -->
    <div v-if="state.showSuccess" class="success fade-up">
      <div class="success-icon">✨</div>
      <div class="success-title header-font">{{ $t('tma.confirmTitle') }}</div>
      <div class="success-sub">{{ $t('tma.confirmSub') }}</div>
      <button class="btn-secondary" style="margin-top: 40px; width: 100%" @click="goHome">{{ $t('tma.goHome') }}</button>
    </div>

    <!-- ══ PAYMENT PENDING ══ -->
    <div v-else-if="state.showPaymentPending" class="success fade-up" style="padding-top: 20px;">
      <div class="success-icon">💳</div>
      <div class="success-title header-font">Ожидаем оплату</div>
      <div class="success-sub">Пожалуйста, завершите оплату в приложении Kaspi Pay. Мы автоматически подтвердим вашу запись, как только получим подтверждение.</div>
      
      <div v-if="state.paymentError" class="card glass mt-6" style="border-color: #ef4444; color: #ef4444; padding: 16px;">
        {{ state.paymentError }}
      </div>

      <div class="flex flex-col gap-4 mt-10 w-full">
        <button class="btn-kaspi" @click="openPaymentLink">
          <div class="kaspi-logo">
            <KaspiQrLogo :white="true" />
          </div>
          <span>{{ $t('tma.payWithKaspi', 'Оплатить с Kaspi.kz') }}</span>
        </button>
        <button class="btn-secondary" @click="cancelPaymentPending">
          {{ $t('common.cancel') }}
        </button>
      </div>

      <div class="mt-8 text-xs text-muted opacity-50 flex items-center justify-center gap-2">
        <div class="spinner-mini" style="border-radius: 50%; border: 2px solid rgba(0,0,0,0.1); border-top-color: var(--gold); width: 14px; height: 14px; animation: spin 1s linear infinite;"></div>
        Проверка статуса платежа...
      </div>
    </div>

    <!-- ══ HOME PAGE ══ -->
    <div v-else-if="state.page === 'home'" class="fade-up">

      <!-- Tabs -->
      <div class="tabs">
        <label class="tab" :class="{ active: state.activeTab === 'services' }" @click="state.activeTab = 'services'">
          <span class="tab-icon">✨</span>
          {{ $t('tma.services') }}
        </label>
        <label class="tab" :class="{ active: state.activeTab === 'masters' }" @click="state.activeTab = 'masters'">
          <span class="tab-icon">👤</span>
          {{ $t('tma.masters') }}
        </label>
      </div>

      <!-- Modern Filter Panel (Admin Style) -->
      <div class="filters-panel">
        <div class="panel-main">
          <!-- Toggle Filter Mode (Search) -->
          <button 
            :class="['filter-toggle', { active: isSearchMode }]" 
            @click="toggleSearchMode"
          >
            <Icon :icon="isSearchMode ? 'mdi:magnify-minus-outline' : 'mdi:magnify'" width="20" />
          </button>

          <TransitionGroup name="panel-slide" tag="div" class="panel-content">
            <!-- Default: Date & Category Toggle -->
            <div v-if="!isSearchMode" key="default" class="panel-row-compact">
              <!-- Categories Trigger -->
              <button 
                :class="['date-pill', { active: showCategoryGrid }]" 
                @click="showCategoryGrid = !showCategoryGrid"
              >
                <Icon icon="mdi:tag-outline" width="16" style="margin-right: 4px;" />
                {{ state.selectedCat ? state.selectedCat.name : $t('tma.serviceCategories') }}
              </button>

              <div class="date-scroll-mini">
                <button 
                  :class="['date-pill-mini', { active: state.selectedDate === todayStr }]" 
                  @click="state.selectedDate = todayStr"
                >{{ $t('tma.today') }}</button>
                <button 
                  :class="['date-pill-mini', { active: state.selectedDate === tomorrowStr }]" 
                  @click="state.selectedDate = tomorrowStr"
                >{{ $t('tma.tomorrow') }}</button>
                <div :class="['date-pill-mini custom-date-wrapper', { active: state.selectedDate !== todayStr && state.selectedDate !== tomorrowStr }]">
                   <input type="date" v-model="state.selectedDate" class="date-input-hidden" :min="todayStr" />
                   <span>{{ (state.selectedDate !== todayStr && state.selectedDate !== tomorrowStr) ? formatDateShort(state.selectedDate) : $t('master.date') }}</span>
                </div>
              </div>
            </div>

            <!-- Search Mode -->
            <div v-else key="search" class="active-filters-row">
              <div class="search-input-wrapper flex-1">
                <Icon icon="mdi:magnify" width="18" class="search-icon" />
                <input 
                  v-model="serviceSearchGlobal" 
                  type="text" 
                  class="filter-input-compact" 
                  placeholder="Поиск услуг..."
                  autofocus
                />
              </div>
            </div>
          </TransitionGroup>
        </div>

        <!-- Expandable Categories Grid -->
        <Transition name="panel-expand">
          <div v-if="showCategoryGrid && !isSearchMode" class="expanded-panel-grid">
            <div class="cat-grid-compact">
              <div 
                :class="['cat-tile-mini', { active: !state.selectedCat }]" 
                @click="state.selectedCat = null; showCategoryGrid = false"
              >
                {{ $t('tma.all') }}
              </div>
              <div 
                v-for="cat in categories" :key="cat.id" 
                :class="['cat-tile-mini', { active: state.selectedCat?.id === cat.id }]"
                @click="handleCatClick(cat); showCategoryGrid = false"
              >
                {{ cat.name }}
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Loading State -->
      <div v-if="loading" style="text-align:center; padding: 60px;">
        <div class="spinner"></div>
      </div>

      <!-- Services List (Admin Card Style) -->
      <template v-else-if="state.activeTab === 'services'">
        <div class="services-list mt-4">
          <div v-if="filteredServicesGlobal.length === 0" class="empty-state">
            <Icon icon="mdi:magnify-close" width="48" class="text-muted opacity-20 mb-2" />
            <p>{{ $t('services.empty') }}</p>
          </div>
          <div v-for="svc in filteredServicesGlobal" :key="svc.id" class="service-card-premium" @click="handleServiceSelect(svc)">
            <div class="service-card-content">
              <div class="service-top-row">
                <div class="service-name-group">
                  <span v-if="svc.is_combo" class="combo-badge-mini">
                    <Icon icon="mdi:link-variant" width="10" />
                  </span>
                  <div class="service-name-text">{{ svc.name }}</div>
                </div>
                <div class="service-price-tag">
                  <template v-if="svc.is_floating_price">{{ svc.price_min }} — {{ svc.price_max }} ₸</template>
                  <template v-else>{{ svc.total_price }} ₸</template>
                </div>
              </div>
              <div class="service-bottom-row">
                <div class="service-meta-info">
                  <Icon icon="mdi:clock-outline" width="14" />
                  <span>{{ svc.duration_minutes }} {{ $t('tma.minutes') }}</span>
                </div>
                <div class="service-arrow">
                  <Icon icon="mdi:chevron-right" width="20" />
                </div>
              </div>
            </div>
          </div>

          <!-- Pagination Controls -->
          <div v-if="services.length > 0" class="pagination-footer mt-6 flex flex-col gap-4">
              <div class="flex items-center justify-between text-xs text-muted px-2">
                  <span>{{ $t('admin.pageSize') || 'Показывать по:' }}</span>
                  <div class="flex gap-2">
                      <button v-for="size in [20, 50]" :key="size" 
                              class="size-pill" 
                              :class="{ active: pageSize === size }"
                              @click="pageSize = size; onPageSizeChange()">
                          {{ size }}
                      </button>
                  </div>
              </div>
              
              <div class="flex items-center justify-center gap-4">
                  <button class="btn-page" :disabled="currentPage === 1" @click="prevPage">
                      <Icon icon="mdi:chevron-left" width="24" />
                  </button>
                  <div class="page-indicator">
                      <b>{{ currentPage }}</b> / {{ totalPages }}
                  </div>
                  <button class="btn-page" :disabled="currentPage >= totalPages" @click="nextPage">
                      <Icon icon="mdi:chevron-right" width="24" />
                  </button>
              </div>
              <div class="text-[10px] text-center text-muted uppercase tracking-widest">
                  Всего: {{ totalCount }}
              </div>
          </div>
        </div>
      </template>

      <!-- Masters tab -->
      <template v-else-if="state.activeTab === 'masters'">
        <div class="master-grid mt-4">
          <div v-for="m in filteredMasters" :key="m.id" 
               :class="['master-card', { 'is-self': isSelf(m) }]" 
               @click="!isSelf(m) && handleMasterFirstSelect(m)">
            <div class="master-photo">
               <img v-if="m.photo_url" :src="m.photo_url" />
               <span v-else>👤</span>
            </div>
            <div class="master-info">
              <div class="master-name">{{ m.first_name }} {{ m.last_name }} <span v-if="isSelf(m)" class="self-badge">({{ $t('tma.itIsYou', 'Это вы') }})</span></div>
              <div class="master-rating">★ 5.0</div>
            </div>
            <div class="flex items-center gap-2">
                <button class="info-trigger" @click.stop="openProfile(m)">
                    <Icon icon="mdi:information-outline" width="22" />
                </button>
                <Icon v-if="!isSelf(m)" icon="mdi:chevron-right" width="24" :style="{ color: 'var(--muted)' }" />
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- ══ SERVICE LIST ══ (Used when choosing master first) -->
    <div v-else-if="state.page === 'service-list'" class="fade-up">
      <div class="page-header">
        <button class="back-btn" @click="goHome">
            <Icon icon="mdi:arrow-left" width="20" />
        </button>
        <div class="page-title header-font">{{ state.selectedMaster ? state.selectedMaster.first_name + ' ' + state.selectedMaster.last_name : $t('tma.services') }}</div>
      </div>
      <div class="services-list mt-2">
        <div v-if="services.length === 0" class="empty-state">
          <Icon icon="mdi:magnify-close" width="48" class="text-muted opacity-20 mb-2" />
          <p>{{ $t('services.empty') }}</p>
        </div>
        <div v-for="svc in services" :key="svc.id" class="service-card-premium" @click="handleServiceSelect(svc)">
            <div class="service-card-content">
              <div class="service-top-row">
                <div class="service-name-group">
                  <span v-if="svc.is_combo" class="combo-badge-mini">
                    <Icon icon="mdi:link-variant" width="10" />
                  </span>
                  <div class="service-name-text">{{ svc.name }}</div>
                </div>
                <div class="service-price-tag">
                  <template v-if="svc.is_floating_price">{{ svc.price_min }} — {{ svc.price_max }} ₸</template>
                  <template v-else>{{ svc.total_price }} ₸</template>
                </div>
              </div>
              <div class="service-bottom-row">
                <div class="service-meta-info">
                  <Icon icon="mdi:clock-outline" width="14" />
                  <span>{{ svc.duration_minutes }} {{ $t('tma.minutes') }}</span>
                </div>
                <div class="service-arrow">
                  <Icon icon="mdi:chevron-right" width="20" />
                </div>
              </div>
            </div>
        </div>

        <!-- Pagination for Service List page -->
        <div v-if="services.length > 0" class="pagination-footer mt-6 flex flex-col gap-4">
            <div class="flex items-center justify-between text-xs text-muted px-2">
                <span>{{ $t('admin.pageSize') || 'Показывать по:' }}</span>
                <div class="flex gap-2">
                    <button v-for="size in [20, 50]" :key="size" 
                            class="size-pill" 
                            :class="{ active: pageSize === size }"
                            @click="pageSize = size; onPageSizeChange()">
                        {{ size }}
                    </button>
                </div>
            </div>
            
            <div class="flex items-center justify-center gap-4">
                <button class="btn-page" :disabled="currentPage === 1" @click="prevPage">
                    <Icon icon="mdi:chevron-left" width="24" />
                </button>
                <div class="page-indicator">
                    <b>{{ currentPage }}</b> / {{ totalPages }}
                </div>
                <button class="btn-page" :disabled="currentPage >= totalPages" @click="nextPage">
                    <Icon icon="mdi:chevron-right" width="24" />
                </button>
            </div>
            <div class="text-[10px] text-center text-muted uppercase tracking-widest">
                Всего: {{ totalCount }}
            </div>
        </div>
      </div>
    </div>

    <!-- ══ MASTER SELECT ══ -->
    <div v-else-if="state.page === 'master-select'" class="fade-up">
      <div class="page-header">
        <button class="back-btn" @click="state.page = 'service-list'">
            <Icon icon="mdi:arrow-left" width="20" />
        </button>
        <div class="page-title header-font">{{ $t('tma.chooseMaster') }}</div>
      </div>
      
      <div v-if="state.selectedService" class="card glass" style="margin-bottom: 20px; border-left: 4px solid var(--gold);">
        <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--gold); font-weight: 800; margin-bottom: 4px;">{{ $t('admin.serviceDetails') }}</div>
        <div style="font-weight: 600;">{{ state.selectedService.name }}</div>
        <div style="font-size: 13px; color: var(--muted); margin-top: 2px;">{{ state.selectedService.total_price }} ₸ • {{ state.selectedService.duration_minutes }} {{ $t('tma.minutes') }}</div>
      </div>

      <div class="master-grid">
        <div v-for="m in masterOptions" :key="m.id" 
             :class="['master-card', { 'is-self': isSelf(m) }]" 
             @click="!isSelf(m) && handleMasterSelect(m)">
            <div class="master-photo">
               <img v-if="m.photo_url" :src="m.photo_url" />
               <span v-else>👤</span>
            </div>
            <div class="master-info">
              <div class="master-name">{{ m.first_name }} {{ m.last_name }} <span v-if="isSelf(m)" class="self-badge">({{ $t('tma.itIsYou') }})</span></div>
              <div class="master-status">{{ $t('tma.availableToday') }}</div>
            </div>
            <div class="flex items-center gap-2">
                <button class="info-trigger" @click.stop="openProfile(m)">
                    <Icon icon="mdi:information-outline" width="22" />
                </button>
                <button v-if="!isSelf(m)" class="status-badge confirmed" style="border: none; cursor: pointer;">{{ $t('common.select') }}</button>
            </div>
        </div>
      </div>
    </div>

    <!-- ══ SLOTS ══ -->
    <div v-else-if="state.page === 'slots'" class="fade-up">
      <div class="page-header">
        <button class="back-btn" @click="state.selectedService ? (state.selectedCat ? (state.page = 'master-select') : (state.page = 'service-list')) : (state.page = 'home')">
            <Icon icon="mdi:arrow-left" width="20" />
        </button>
        <div class="page-title header-font">{{ $t('tma.chooseTime') }}</div>
      </div>

      <div class="page-header" style="margin-bottom: 24px; gap: 8px; overflow-x: auto; padding-bottom: 4px;">
        <div class="date-pill" :class="{ active: state.selectedDate === todayStr }" @click="state.selectedDate = todayStr">{{ $t('tma.today') }}</div>
        <div class="date-pill" :class="{ active: state.selectedDate === tomorrowStr }" @click="state.selectedDate = tomorrowStr">{{ $t('tma.tomorrow') }}</div>
        <div class="custom-date-wrapper">
           <div :class="['date-pill', { active: state.selectedDate !== todayStr && state.selectedDate !== tomorrowStr }]">
              {{ (state.selectedDate !== todayStr && state.selectedDate !== tomorrowStr) ? formatDateShort(state.selectedDate) : $t('master.date') }}
           </div>
           <input type="date" class="date-input-hidden" v-model="state.selectedDate" :min="todayStr" />
        </div>
      </div>

      <div v-if="slotsLoading" style="text-align:center; padding: 40px;">
         <div class="spinner"></div>
      </div>
      
      <div v-else-if="shiftClosed" class="card glass fade-up" style="text-align: center; border-color: #ef4444; padding: 32px 20px;">
         <div style="font-size: 40px; margin-bottom: 16px">🚫</div>
         <div style="font-weight: 700; font-size: 18px; margin-bottom: 8px;">{{ $t('tma.shiftNotStarted') }}</div>
         <div style="color: var(--muted); font-size: 14px; margin-bottom: 16px;">{{ $t('tma.masterNotWorkingYet') }}</div>
         <div v-if="suggestedDate" class="fade-up">
           <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--gold); letter-spacing: 0.5px; margin-bottom: 8px;">Ближайший рабочий день:</div>
           <button class="btn-primary" style="margin: 0 auto; width: auto; font-size: 13px; padding: 8px 16px;" @click="state.selectedDate = suggestedDate">
             Посмотреть {{ formatDateShort(suggestedDate) }}
           </button>
         </div>
      </div>

      <div v-else-if="slots.length === 0" style="text-align:center; padding: 40px; color: var(--muted)">
         <Icon icon="mdi:calendar-blank" width="48" style="opacity: 0.2; margin-bottom: 12px" />
         <div>{{ $t('tma.noSlots') }}</div>
      </div>

      <div v-else class="slot-grid">
        <div v-for="s in slots" :key="s.time" 
             class="slot" 
             :class="{ 
                selected: state.selectedSlot && state.selectedSlot.time === s.time, 
                busy: s.status === 'busy',
                lunch: s.status === 'lunch',
                limit: s.status === 'limit'
             }" 
             @click="s.is_available ? handleSlotSelect(s) : null">
          {{ s.time }}
        </div>
      </div>
    </div>

    <!-- ══ CONFIRMATION MODAL ══ -->
    <div v-if="state.showModal && state.selectedService && state.selectedMaster && state.selectedSlot" 
         class="modal-overlay" @click.self="state.showModal = false">
       <div class="modal">
        <div class="modal-title header-font">{{ $t('tma.confirmBooking') }}</div>
        
        <div class="card glass" style="margin-bottom: 24px; text-align: left;">
             <div class="modal-row">
               <span class="modal-label">{{ $t('services.title') }}</span>
               <span class="modal-value">{{ state.selectedService.name }}</span>
             </div>
              <div class="modal-row">
                <span class="modal-label">{{ $t('tma.masters') }}</span>
                <span class="modal-value">
                  {{ state.selectedMaster.first_name }} {{ state.selectedMaster.last_name }}
                  <span v-if="state.selectedService.is_combo" style="color: var(--gold); font-size: 11px; display: block; text-align: right;">
                    (+1 {{ $t('tma.freeMaster', 'свободный мастер') }})
                  </span>
                </span>
              </div>
             <div class="modal-row">
               <span class="modal-label">{{ $t('common.time') }}</span>
                <span class="modal-value">{{ state.selectedDate }}, {{ state.selectedSlot.time }}</span>
             </div>
              <div class="modal-row" style="border-bottom: none; margin-top: 12px;">
                <span class="modal-label" style="font-size: 16px; color: var(--text); font-weight: 700;">{{ $t('tma.total') }}</span>
                <span class="modal-value gold header-font" style="font-size: 22px;">
                  <template v-if="state.selectedService.is_floating_price">{{ state.selectedService.price_min }} — {{ state.selectedService.price_max }} ₸</template>
                  <template v-else>{{ state.selectedService.total_price }} ₸</template>
                </span>
              </div>
         </div>
         
         <button v-if="auth.organizationSettings?.is_prepayment_enabled && state.selectedService?.is_prepayment_required" 
                 class="btn-kaspi" 
                 @click="handleConfirm" 
                 :disabled="state.paymentLoading"
                 style="margin-top: 24px;">
            <template v-if="state.paymentLoading">
              <div class="spinner-mini" style="display:inline-block; margin-right: 8px;"></div>
              {{ $t('common.loading') }}
            </template>
            <template v-else>
              <div class="kaspi-logo">
                <KaspiQrLogo :white="true" />
              </div>
              <span>{{ $t('tma.payWithKaspi', 'Оплатить с Kaspi.kz') }}</span>
            </template>
         </button>
         <button v-else class="btn-confirm" @click="handleConfirm">
            {{ $t('tma.book') }}
          </button>
         <button class="btn-secondary" style="margin-top: 12px; width: 100%" @click="state.showModal = false">
           {{ $t('common.cancel') }}
         </button>
      </div>
    </div>

    <!-- ══ PHONE CONFIRMATION MODAL ══ -->
    <div v-if="state.showPhoneConfirm" class="modal-overlay" @click.self="state.showPhoneConfirm = false">
       <div class="modal">
         <div class="modal-title header-font">{{ $t('tma.prepayment.title') }}</div>
         <p class="text-center text-muted mb-6" v-html="$t('tma.prepayment.requiredText', { amount: state.prepaymentAmount })"></p>
         
         <div v-if="auth.user?.phone && !state.editingPhone" class="card glass mb-6 text-center">
            <p class="text-xs uppercase tracking-widest opacity-50 mb-2">{{ $t('tma.prepayment.invoiceToPhone') }}</p>
            <p class="text-xl font-bold">{{ auth.user.phone }}</p>
            <div class="flex gap-2 mt-4">
               <button class="btn-confirm" style="margin-top:0" @click="confirmWithCurrentPhone">{{ $t('tma.prepayment.yesThisOne') }}</button>
               <button class="btn-secondary" style="margin-top:0" @click="state.editingPhone = true">{{ $t('tma.prepayment.otherPhone') }}</button>
            </div>
         </div>

         <div v-else class="w-full">
            <label class="block text-xs font-bold uppercase mb-2">{{ $t('tma.prepayment.phoneLabel') }}</label>
            <input 
              v-model="state.clientPhone" 
              type="tel" 
              class="filter-input-compact" 
              placeholder="+7 (___) ___-__-__"
              style="padding-left: 12px; height: 50px; font-size: 18px;"
            />
            <button class="btn-confirm" @click="confirmWithNewPhone" :disabled="!state.clientPhone">
               {{ $t('common.continue') }}
            </button>
         </div>
         
         <button class="btn-secondary mt-2 w-full" @click="state.showPhoneConfirm = false">
           {{ $t('common.cancel') }}
         </button>
       </div>
    </div>

    <!-- ══ MANUAL PAYMENT SUCCESS ══ -->
    <div v-if="state.showManualSuccess" class="success fade-up">
      <div class="success-icon">📜</div>
      <div class="success-title header-font">{{ $t('tma.prepayment.bookingCreated') }}</div>
      <div class="success-sub">
        <div v-html="$t('tma.prepayment.kaspiInvoiceText', { phone: state.clientPhone })"></div>
        <div v-html="$t('tma.prepayment.amount', { amount: state.prepaymentAmount })" class="mt-2"></div>
        <div class="mt-2">{{ $t('tma.prepayment.autoConfirmText') }}</div>
      </div>
      <button class="btn-secondary" style="margin-top: 40px; width: 100%" @click="goHome">{{ $t('tma.goHome') }}</button>
    </div>
    
    <!-- ══ MASTER PROFILE MODAL ══ -->
    <div v-if="state.showProfileModal && state.profileMaster" 
         class="modal-overlay" @click.self="state.showProfileModal = false">
       <div class="modal h-80vh">
          <div class="modal-header-actions">
            <div class="modal-title header-font">{{ $t('tma.masterProfile') }}</div>
            <button class="close-modal-btn" @click="state.showProfileModal = false">
                <Icon icon="mdi:close" width="24" />
            </button>
          </div>
          
          <div class="modal-scroll-content">
             <div class="profile-hero-premium">
                <div class="profile-photo-rect">
                   <img v-if="state.profileMaster.photo_url" :src="state.profileMaster.photo_url" />
                   <div v-else class="photo-placeholder">👤</div>
                </div>
                <div class="profile-header-info">
                   <h2 class="profile-name header-font">{{ state.profileMaster.first_name }} {{ state.profileMaster.last_name }}</h2>
                   <div class="profile-badges">
                      <span class="badge-outline">120+ {{ $t('owner.records') }}</span>
                   </div>
                </div>
             </div>
             
             <div v-if="state.profileMaster.bio" class="profile-section">
                <div class="section-label">{{ $t('tma.aboutMaster') }}</div>
                <div class="profile-bio markdown-content" v-html="renderedBio"></div>
             </div>
             
             <div class="profile-section">
                <div class="section-label">{{ $t('services.title') }}</div>
                <div class="profile-services-list">
                   <div v-for="s_id in state.profileMaster.services" :key="s_id" class="mini-service-tag">
                      {{ services.find(sx => sx.id === s_id)?.name || 'Услуга' }}
                   </div>
                </div>
             </div>
          </div>
          
          <div class="modal-footer">
             <button class="btn-confirm" @click="selectFromProfile">
               {{ $t('common.select') }}
             </button>
          </div>
       </div>
    </div>

  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { Icon } from '@iconify/vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import KaspiQrLogo from '@/components/common/KaspiQrLogo.vue'

const router = useRouter()
const auth = useAuthStore()

const getTodayStr = () => new Date().toISOString().slice(0,10)
const getTomorrowStr = () => {
  const d = new Date(); d.setDate(d.getDate()+1);
  return d.toISOString().slice(0,10)
}

const todayStr = getTodayStr()
const tomorrowStr = getTomorrowStr()

const formatDateShort = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString([], { day: 'numeric', month: 'short' })
}

const state = reactive({
  page: 'home',
  activeTab: 'services',
  selectedDate: todayStr,
  selectedCat: null,
  selectedService: null,
  selectedMaster: null,
  selectedSlot: null,
  masterFilter: null,
  showProfileModal: false,
  profileMaster: null,
  // Payment state
  paymentLoading: false,
  paymentLink: null,
  paymentId: null,
  paymentError: null,
  showPaymentPending: false,
  paymentMethod: null,
  paymentStatus: 'pending_receipt',
  // Prepayment mode state
  showPhoneConfirm: false,
  prepaymentAmount: 0,
  clientPhone: '',
  showManualSuccess: false
})

const categories = ref([])
const services = ref([])
const masters = ref([])
const loading = ref(true)

const slots = ref([])
const slotsLoading = ref(false)
const shiftClosed = ref(false)
const suggestedDate = ref(null)

// ── Filters State ──────────────────────────────────────────────
const isSearchMode = ref(false)
const showCategoryGrid = ref(false)
const serviceSearchGlobal = ref('')
const masterSearchQuery = ref('')

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value) || 1)

const toggleSearchMode = () => {
  isSearchMode.value = !isSearchMode.value
  if (!isSearchMode.value) {
    serviceSearchGlobal.value = ''
  } else {
    showCategoryGrid.value = false
  }
}

const filteredServicesGlobal = computed(() => {
  return services.value
})

const hasActiveMastersFilters = computed(() => {
  return state.masterFilter || masterSearchQuery.value
})

const fetchServices = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: serviceSearchGlobal.value,
      category: state.selectedCat?.id || '',
      master_id: state.selectedMaster?.id || ''
    }
    const servsRes = await api.get('/services/', { params })
    if (servsRes.data.results) {
        services.value = servsRes.data.results
        totalCount.value = servsRes.data.count
    } else {
        services.value = Array.isArray(servsRes.data) ? servsRes.data : []
        totalCount.value = services.value.length
    }
  } catch (e) {
    console.error('Servs fetch fail', e)
    services.value = []
  } finally {
    loading.value = false
  }
}

const fetchData = async () => {
  try {
    loading.value = true
    
    // Attempt to fetch categories
    try {
      const catsRes = await api.get('/categories/', { params: { page_size: 1000 } })
      categories.value = catsRes.data.results || catsRes.data
    } catch (e) { console.error('Cats fetch fail', e) }

    // Fetch initial services
    await fetchServices()

    // Attempt to fetch masters
    try {
      const mastersRes = await api.get('/masters/', { params: { page_size: 1000 } })
      masters.value = mastersRes.data.results || mastersRes.data
    } catch (e) { console.error('Masters fetch fail', e) }

    if (!auth.organizationSettings) {
      await auth.fetchCurrentUser()
    }

    // Parse startapp / start_param for deep links
    let startParam = null
    if (window.Telegram && window.Telegram.WebApp) {
      startParam = window.Telegram.WebApp.initDataUnsafe?.start_param || null
    } else {
      const urlParams = new URLSearchParams(window.location.search)
      startParam = urlParams.get('startapp') || urlParams.get('start_param')
    }

    if (startParam) {
      if (startParam.startsWith('cat_')) {
        const catId = parseInt(startParam.split('_')[1], 10)
        const category = categories.value.find(c => c.id === catId)
        if (category) {
          state.selectedCat = category
          state.page = 'home'
          state.activeTab = 'services'
          showCategoryGrid.value = false
        }
      } else if (startParam.startsWith('ser_')) {
        const serId = parseInt(startParam.split('_')[1], 10)
        let service = services.value.find(s => s.id === serId)
        if (!service) {
          try {
            const res = await api.get(`/services/${serId}/`)
            service = res.data
          } catch (err) {
            console.error('Failed to fetch service for deep link', err)
          }
        }
        if (service) {
          state.selectedService = service
          state.page = 'master-select'
        }
      } else if (startParam.startsWith('mas_')) {
        const masId = parseInt(startParam.split('_')[1], 10)
        let master = masters.value.find(m => m.id === masId)
        if (!master) {
          try {
            const res = await api.get(`/masters/${masId}/`)
            master = res.data
          } catch (err) {
            console.error('Failed to fetch master for deep link', err)
          }
        }
        if (master) {
          state.selectedMaster = master
          state.profileMaster = master
          state.showProfileModal = true
          state.page = 'service-list'
        }
      }
    }
  } catch (err) {
    console.error('General Fetch error:', err)
  } finally {
    loading.value = false
  }
}

// Watchers for server-side filtering
let debounceTimer = null
watch(serviceSearchGlobal, () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
        currentPage.value = 1
        fetchServices()
    }, 400)
})

watch(() => state.selectedCat, () => {
    currentPage.value = 1
    fetchServices()
})

const onPageSizeChange = () => {
    currentPage.value = 1
    fetchServices()
}

const nextPage = () => {
    if (currentPage.value < totalPages.value) {
        currentPage.value++
        fetchServices()
    }
}

const prevPage = () => {
    if (currentPage.value > 1) {
        currentPage.value--
        fetchServices()
    }
}

onMounted(() => {
  fetchData()
})

const catServices = computed(() => {
  if (!services.value) return []
  
  let baseServices = services.value
  
  // Filter by category if one is selected
  if (state.selectedCat) {
    const targetCatId = String(state.selectedCat.id || state.selectedCat)
    baseServices = baseServices.filter(s => {
      const sCatId = s.category?.id || s.category
      return String(sCatId) === targetCatId
    })
  }
    
  if (state.selectedMaster) {
    const masterServices = state.selectedMaster.services || []
    baseServices = baseServices.filter(s => masterServices.includes(s.id))
  }
  
  return baseServices
})

const masterOptions = computed(() => {
    if (!state.selectedService) return masters.value.filter(m => !m.is_virtual)
    return masters.value.filter(m => !m.is_virtual && m.services?.includes(state.selectedService.id))
})

const filteredMasters = computed(() => {
  let result = masters.value.filter(m => !m.is_virtual)
  
  if (state.masterFilter) {
    result = result.filter(m => m.services?.some(s => {
      const svc = services.value.find(sx => sx.id === s)
      return svc && svc.category === state.masterFilter
    }))
  }

  if (masterSearchQuery.value) {
    const q = masterSearchQuery.value.toLowerCase()
    result = result.filter(m => {
      const full = (m.first_name + ' ' + (m.last_name || '')).toLowerCase()
      return full.includes(q)
    })
  }

  return result
})

const isSelf = (master) => {
  if (!auth.user || !master.user) return false
  return auth.user.id === master.user
}

const goHome = () => {
  state.page = 'home'
  state.selectedCat = null
  state.selectedService = null
  state.selectedMaster = null
  state.selectedSlot = null
  state.showSuccess = false
}

const handleCatClick = (cat) => {
  state.selectedCat = cat
}

const handleServiceSelect = (svc) => {
  state.selectedService = svc
  if (state.selectedMaster) {
    state.page = 'slots'
  } else {
    state.page = 'master-select'
  }
}

const handleMasterSelect = (master) => {
  state.selectedMaster = master
  state.page = 'slots'
}

const handleSlotSelect = (slot) => {
  state.selectedSlot = slot
  state.showModal = true
}

const handleMasterFirstSelect = (master) => {
  state.selectedMaster = master
  state.selectedCat = null 
  state.page = 'service-list'
}

const fetchSlots = async () => {
  if (!state.selectedMaster || !state.selectedService || !state.selectedDate) return
  try {
    slotsLoading.value = true
    shiftClosed.value = false
    suggestedDate.value = null
    slots.value = []
    
    const res = await api.get(`/masters/${state.selectedMaster.id}/available-slots/`, {
      params: {
        date: state.selectedDate,
        service_id: state.selectedService.id
      }
    })
    slots.value = res.data
  } catch (err) {
    if (err.response?.status === 400 && err.response?.data?.error === 'shift_closed') {
        shiftClosed.value = true
        try {
          const today = new Date().toISOString().slice(0, 10)
          const shiftsRes = await api.get('/master-shifts/', {
            params: {
              master_id: state.selectedMaster.id,
              date_from: today,
              is_open: 'true',
              page_size: 10
            }
          })
          const shifts = shiftsRes.data.results || shiftsRes.data || []
          if (shifts.length > 0) {
            const sortedShifts = shifts.filter(s => s.date > state.selectedDate).sort((a, b) => a.date.localeCompare(b.date))
            if (sortedShifts.length > 0) {
              suggestedDate.value = sortedShifts[0].date
            } else {
              suggestedDate.value = shifts[0].date
            }
          }
        } catch (shiftErr) {
          console.error('Failed to load next master shifts:', shiftErr)
        }
    } else {
        console.error('Fetch slots error:', err)
    }
  } finally {
    slotsLoading.value = false
  }
}

const openProfile = (m) => {
  state.profileMaster = m
  state.showProfileModal = true
}

const selectFromProfile = () => {
    const m = state.profileMaster
    state.showProfileModal = false
    if (state.selectedService) {
        handleMasterSelect(m)
    } else {
        handleMasterFirstSelect(m)
    }
}

const renderedBio = computed(() => {
  if (!state.profileMaster?.bio) return ''
  let html = state.profileMaster.bio
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3 style="font-size: 16px; font-weight: 700; margin: 12px 0 6px;">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size: 18px; font-weight: 700; margin: 16px 0 8px;">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="font-size: 20px; font-weight: 700; margin: 16px 0 8px;">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li style="margin-left: 16px;">$1</li>')
    .replace(/\n\n/g, '</p><p style="margin-bottom: 8px;">')
    .replace(/\n/g, '<br/>')
  return `<p>${html}</p>`
})

watch([() => state.selectedMaster, () => state.selectedService, () => state.selectedDate, () => state.page], () => {
    if (state.selectedMaster && ['slots'].includes(state.page)) {
        fetchSlots()
    }
    // Refresh services if master or category selection changes on sub-pages
    if (['service-list'].includes(state.page)) {
        currentPage.value = 1
        fetchServices()
    }
})

const { t } = useI18n()

const handleConfirm = async () => {
  try {
    const slot = state.selectedSlot
    const date = state.selectedDate
    const service = state.selectedService
    const master = state.selectedMaster

    if (!slot || !date || !service || !master) {
      alert(t('tma.error'))
      return
    }

    const startTime = slot.start_iso || `${date}T${slot.time}:00+05:00`
    
    let endTime = slot.end_iso
    if (!endTime) {
        const duration = service.duration_minutes || 30
        const d = new Date(`${date}T${slot.time}:00+05:00`)
        d.setMinutes(d.getMinutes() + duration)
        const pad = (n) => n.toString().padStart(2, '0')
        endTime = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00+05:00`
    }

    const res = await api.post('/appointments/', {
      master: master.id,
      service: service.id,
      start_time: startTime,
      end_time: endTime
    })
    
    const appointmentId = res.data.id
    
    // Check if prepayment is required for this SERVICE
    if (service.is_prepayment_required) {
      state.showModal = false
      state.prepaymentAmount = res.data.prepayment_amount_required || 0
      state.currentAppointmentId = appointmentId
      
      const method = auth.organizationSettings?.payment_method || 'MANUAL'
      if (method === 'SEMI_AUTOMATIC') {
        state.clientPhone = auth.user?.phone || ''
        await initiatePayment()
      } else {
        state.showPhoneConfirm = true
      }
      return
    }

    state.showModal = false
    state.showSuccess = true
  } catch (error) {
    const errorMsg = error.response?.data?.error || error.response?.data?.detail || t('tma.error')
    alert(errorMsg)
  }
}

let paymentPollInterval = null
const startPaymentPolling = () => {
  if (paymentPollInterval) clearInterval(paymentPollInterval)
  paymentPollInterval = setInterval(async () => {
    if (!state.paymentId || !state.showPaymentPending) {
      clearInterval(paymentPollInterval)
      return
    }
    
    try {
      const res = await api.get(`/payments/status/${state.paymentId}/`)
      state.paymentStatus = res.data.status
      
      if (res.data.status === 'paid') {
        clearInterval(paymentPollInterval)
        state.showPaymentPending = false
        state.showSuccess = true
      } else if (res.data.status === 'Error') {
        clearInterval(paymentPollInterval)
        state.paymentError = 'Ошибка оплаты. Попробуйте еще раз или свяжитесь с нами.'
      }
    } catch (e) {
      console.error('Poll error', e)
    }
  }, 180000) // Poll every 3 minutes
}

const confirmWithCurrentPhone = () => {
  state.clientPhone = auth.user.phone
  initiatePayment()
}

const confirmWithNewPhone = () => {
  if (!state.clientPhone) return
  initiatePayment()
}

const initiatePayment = async () => {
  try {
    state.paymentLoading = true
    const payRes = await api.post('/payments/create-link/', { 
        appointment_id: state.currentAppointmentId,
        client_phone: state.clientPhone
    })
    
    state.showPhoneConfirm = false
    
    if (payRes.data.manual_mode) {
        state.showManualSuccess = true
    } else if (payRes.data.payment_method === 'SEMI_AUTOMATIC') {
        router.push({ name: 'payment-instruction', params: { appointmentId: state.currentAppointmentId } })
        
        if (payRes.data.payment_link) {
          try {
            if (window.Telegram?.WebApp && typeof window.Telegram.WebApp.openLink === 'function') {
              window.Telegram.WebApp.openLink(payRes.data.payment_link)
            } else {
              window.open(payRes.data.payment_link, '_blank')
            }
          } catch (openErr) {
            console.error('Failed to open payment link:', openErr)
          }
        }
    } else {
        state.paymentLink = payRes.data.payment_link
        state.paymentId = payRes.data.payment_id
        state.paymentMethod = payRes.data.payment_method
        state.prepaymentAmount = payRes.data.prepayment_amount
        state.paymentStatus = 'pending_receipt'
        
        state.showPaymentPending = true
        startPaymentPolling()

        if (state.paymentLink) {
          try {
            if (window.Telegram?.WebApp && typeof window.Telegram.WebApp.openLink === 'function') {
              window.Telegram.WebApp.openLink(state.paymentLink)
            } else {
              window.open(state.paymentLink, '_blank')
            }
          } catch (openErr) {
            console.error('Failed to open payment link:', openErr)
          }
        }
    }
  } catch (payErr) {
    console.error('Payment link creation failed', payErr)
    alert('Не удалось создать ссылку на оплату. Пожалуйста, обратитесь в салон.')
    goHome()
  } finally {
    state.paymentLoading = false
  }
}

const openPaymentLink = () => {
  if (!state.paymentLink) return
  try {
    if (window.Telegram?.WebApp && typeof window.Telegram.WebApp.openLink === 'function') {
      window.Telegram.WebApp.openLink(state.paymentLink)
    } else {
      window.open(state.paymentLink, '_blank')
    }
  } catch (openErr) {
    console.error('Failed to open payment link in button click:', openErr)
  }
}

const cancelPaymentPending = () => {
  state.showPaymentPending = false
  if (paymentPollInterval) clearInterval(paymentPollInterval)
  goHome()
}
</script>

<style scoped>
.home-view { padding: 20px 16px; }

/* Tabs */
.tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.tab {
  flex: 1; padding: 14px 8px; border-radius: var(--radius-sm);
  background: var(--card-bg); border: 1px solid var(--border);
  cursor: pointer; text-align: center; transition: all .2s;
  font-size: 13px; font-weight: 600; color: var(--muted);
}
.tab.active { background: var(--gold-gradient); color: #000; border-color: var(--gold); box-shadow: 0 4px 12px var(--gold-glow); }
.tab-icon { font-size: 20px; display: block; margin-bottom: 4px; }

/* Modern Filter Panel (Admin Style) */
.filters-panel {
  background: var(--bg-secondary);
  border-radius: 18px;
  padding: 6px;
  margin-bottom: 20px;
  border: 1px solid var(--border);
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

.panel-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-toggle {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: var(--tg-bg);
  border: 1px solid var(--border);
  color: var(--text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.filter-toggle.active {
  background: var(--gold-gradient);
  color: #000;
  border-color: var(--gold);
}

.panel-content {
  flex: 1;
  display: flex;
  align-items: center;
  height: 40px;
  overflow: hidden;
}

.panel-row-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.date-scroll-mini {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  flex: 1;
}
.date-pill-mini {
  white-space: nowrap;
  padding: 8px 12px;
  border-radius: 12px;
  background: var(--tg-bg);
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s;
}
.date-pill-mini.active {
  background: var(--gold-gradient);
  color: #000;
  border-color: var(--gold);
}

.date-pill {
  white-space: nowrap;
  padding: 8px 16px;
  border-radius: 20px;
  background: var(--tg-bg);
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.date-pill.active {
  background: var(--gold-accent, rgba(212, 175, 55, 0.15));
  color: var(--gold);
  border-color: var(--gold);
}

.expanded-panel-grid {
  margin-top: 8px;
  padding: 4px;
  background: var(--tg-bg);
  border-radius: 14px;
  border: 1px solid var(--border);
  max-height: 200px;
  overflow-y: auto;
}

.cat-grid-compact {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 4px;
}
.cat-tile-mini {
  padding: 8px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
}
.cat-tile-mini.active {
  background: var(--gold-accent, rgba(212, 175, 55, 0.15));
  color: var(--gold);
  border-color: var(--gold);
}

.active-filters-row {
  display: flex;
  gap: 6px;
  width: 100%;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon {
  position: absolute;
  left: 10px;
  color: var(--muted);
}
.filter-input-compact {
  width: 100%;
  background: var(--tg-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px 10px 10px 34px;
  font-size: 14px;
  color: var(--text);
  outline: none;
}
.filter-input-compact:focus {
  border-color: var(--gold);
}

/* Service Card Premium (Admin Style) */
.services-list { display: flex; flex-direction: column; gap: 12px; }
.service-card-premium {
  background: var(--bg-secondary);
  border-radius: 18px;
  padding: 16px;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.2s;
}
.service-card-premium:active {
  transform: scale(0.98);
  border-color: var(--gold);
}
.spinner {
  width: 32px; height: 32px; border: 3px solid var(--border); border-top-color: var(--gold);
  border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto;
}
.spinner-mini {
  width: 16px; height: 16px; border: 2px solid rgba(0,0,0,0.1); border-top-color: var(--gold);
  border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.service-card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.service-top-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.service-name-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}
.service-name-text {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.3;
}
.service-price-tag {
  font-size: 16px;
  font-weight: 800;
  color: var(--gold);
  white-space: nowrap;
}
.service-bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}
.service-meta-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--muted);
}
.service-arrow {
  color: var(--muted);
  opacity: 0.5;
}

.combo-badge-mini {
  background: var(--gold-gradient);
  color: #000;
  padding: 2px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--muted);
}

.custom-date-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}
.date-input-hidden {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  opacity: 0; cursor: pointer;
}

/* Master grid */
.master-grid { display: flex; flex-direction: column; gap: 10px; }
.master-card {
  background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 16px; display: flex; align-items: center; gap: 16px; cursor: pointer; transition: all .2s;
}
.master-photo { width: 60px; height: 60px; border-radius: 50%; background: var(--bg-secondary); display: flex; align-items: center; justify-content: center; font-size: 32px; flex-shrink: 0; border: 2px solid var(--border); overflow: hidden; }
.master-photo img { width: 100%; height: 100%; object-fit: cover; }
.master-name { font-size: 16px; font-weight: 600; color: var(--text); }
.master-status { font-size: 12px; color: var(--muted); font-weight: 600; }

.master-card.is-self { 
  opacity: 0.7; cursor: default; background: var(--bg-secondary); border-style: dashed;
}
.self-badge { font-size: 11px; color: var(--gold); margin-left: 4px; font-weight: 700; text-transform: uppercase; }

/* Slot grid */
.slot-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin-bottom: 24px; }
.slot {
  padding: 12px 0; border-radius: var(--radius-sm); text-align: center;
  font-size: 14px; cursor: pointer; border: 1px solid var(--border);
  background: var(--card-bg); transition: all 0.2s; font-weight: 600;
}
.slot.busy { background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3); color: #ef4444; text-decoration: line-through; cursor: not-allowed; opacity: 0.6; }
.slot.lunch { background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.3); color: #f59e0b; cursor: not-allowed; opacity: 0.6; }
.slot.limit { opacity: 0.3; background: var(--bg-primary); border-style: dashed; cursor: not-allowed; }
.slot.selected { background: var(--gold-gradient) !important; color: #000 !important; border-color: var(--gold) !important; opacity: 1 !important; text-decoration: none !important; box-shadow: 0 4px 10px var(--gold-glow) !important; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.7); z-index: 500;
  display: flex; align-items: flex-end; justify-content: center;
  backdrop-filter: blur(4px);
}
.modal {
  background: var(--bg); border-radius: 28px 28px 0 0; width: 100%; max-width: 450px;
  padding: 32px 20px 40px; border-top: 1px solid var(--border);
  box-shadow: 0 -10px 40px rgba(0,0,0,0.3);
  max-height: 90vh; display: flex; flex-direction: column;
}
.modal-title { font-size: 24px; font-weight: 700; margin-bottom: 24px; text-align: center; font-family: var(--font-header); }
.modal-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
.modal-label { color: var(--muted); font-weight: 500; }
.modal-value { font-weight: 600; color: var(--text); }
.modal-value.gold { color: var(--gold); font-size: 19px; font-family: var(--font-header); }

/* Buttons */
.btn-confirm {
  width: 100%; margin-top: 24px; padding: 16px; border-radius: var(--radius-sm);
  background: var(--gold-gradient); color: #000; border: none; font-size: 16px;
  font-weight: 700; cursor: pointer; box-shadow: 0 6px 20px var(--gold-glow);
}

.btn-kaspi {
  width: 100%;
  height: 54px;
  background: #F14635;
  border: none;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(241, 70, 53, 0.2);
}
.btn-kaspi:active {
  transform: scale(0.98);
  background: #D63425;
}
.btn-kaspi span {
  font-size: 16px;
  font-weight: 700;
  color: #FFFFFF;
}
.kaspi-logo {
  display: flex;
  align-items: center;
}

.success { text-align: center; padding: 60px 20px; }
.success-icon { font-size: 64px; margin-bottom: 20px; filter: drop-shadow(0 4px 10px var(--gold-glow)); }
.success-title { font-size: 28px; font-weight: 700; margin-bottom: 12px; color: var(--gold); font-family: var(--font-header); }
.success-sub { font-size: 15px; color: var(--muted); line-height: 1.6; }

/* Profile Modal Specifics */
.info-trigger {
  background: var(--bg-secondary); border: 1px solid var(--border);
  color: var(--gold); width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.info-trigger:active { background: var(--gold-glow); transform: scale(0.9); }

.modal-header-actions { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.close-modal-btn { background: none; border: none; color: var(--muted); cursor: pointer; padding: 4px; }

.modal-scroll-content { flex: 1; overflow-y: auto; padding-right: 4px; }
.modal-scroll-content::-webkit-scrollbar { width: 4px; }
.modal-scroll-content::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

/* Premium Profile Styles */
.profile-hero-premium { display: flex; flex-direction: column; gap: 20px; margin-bottom: 24px; }
.profile-photo-rect {
  width: 100%; max-width: 240px; height: 272px; margin: 0 auto;
  border-radius: 24px; overflow: hidden; background: var(--bg-secondary);
  border: 1px solid var(--border); box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  display: flex; align-items: center; justify-content: center;
}
.profile-photo-rect img { width: 100%; height: 100%; object-fit: cover; }
.photo-placeholder { font-size: 80px; opacity: 0.5; }
.profile-header-info { text-align: center; }
.profile-badges { display: flex; justify-content: center; gap: 8px; margin-top: 8px; }
.badge-outline { border: 1px solid var(--border); color: var(--muted); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.profile-name { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
.profile-section { margin-bottom: 24px; }
.section-label { 
  font-size: 11px; font-weight: 800; text-transform: uppercase; 
  letter-spacing: 1px; color: var(--gold); margin-bottom: 10px;
  display: flex; align-items: center; gap: 8px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); opacity: 0.5; }
.profile-bio { line-height: 1.6; color: var(--text); font-size: 15px; }
.profile-services-list { display: flex; flex-wrap: wrap; gap: 8px; }
.mini-service-tag { 
  background: var(--bg-secondary); border: 1px solid var(--border);
  padding: 6px 12px; border-radius: 20px; font-size: 12px; color: var(--muted);
  font-weight: 600;
}
.modal-footer { margin-top: auto; padding-top: 16px; border-top: 1px solid var(--border); }

/* Animations */
.panel-slide-enter-active, .panel-slide-leave-active { transition: all 0.3s ease; }
.panel-slide-enter-from { opacity: 0; transform: translateX(20px); }
.panel-slide-leave-to { opacity: 0; transform: translateX(-20px); }

/* Pagination */
.pagination-footer {
    padding: 0 4px 20px;
}
.size-pill {
    padding: 4px 12px;
    border-radius: 8px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    font-size: 12px;
    color: var(--muted);
    transition: all 0.2s;
}
.size-pill.active {
    background: var(--gold-gradient);
    color: #000;
    border-color: var(--gold);
}
.btn-page {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    color: var(--gold); transition: all 0.2s;
}
.btn-page:disabled { opacity: 0.3; }
.btn-page:active:not(:disabled) { transform: scale(0.9); background: var(--gold-glow); }
.page-indicator { font-size: 16px; color: var(--text); }
.page-indicator b { color: var(--gold); }

@keyframes panel-expand {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.panel-expand-enter-active { animation: panel-expand 0.2s ease-out; }
.panel-expand-leave-active { animation: panel-expand 0.2s ease-in reverse; }
</style>
