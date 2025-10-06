<template>
  <div class="bg-white rounded-lg shadow-md p-4 text-center border border-gray-200 hover:shadow-lg transition-shadow duration-300">
    <!-- Stockpile Name -->
    <div class="font-bold text-brand-dark text-md mb-3 truncate">
      {{ stockpile.name }}
    </div>
    
    <!-- Pile Visualization -->
    <div class="relative w-full h-20 mb-4 flex items-end justify-center">
      <!-- Ground line -->
      <div class="absolute bottom-0 left-1/4 right-1/4 h-0.5 bg-gray-400"></div>
      
      <!-- Material pile -->
      <div class="relative pile-container">
        <!-- Main pile shape -->
        <div 
          v-if="Math.round(stockpile.utilization_percent) > 0"
          class="pile-shape transition-all duration-700 ease-out"
          :style="{
            height: `${Math.max(6, stockpile.utilization_percent * 0.6)}px`,
            width: `${Math.max(20, stockpile.utilization_percent * 1.0)}px`,
            backgroundColor: getUtilizationColor(stockpile.utilization_percent),
          }"
        ></div>
        
        <!-- Pile texture/particles for visual interest -->
        <div 
          v-if="Math.round(stockpile.utilization_percent) > 0"
          v-for="n in getParticleCount(stockpile.utilization_percent)" 
          :key="n"
          class="pile-particle"
          :style="{
            left: `${getRandomPosition(n, 'x')}%`,
            top: `${getRandomPosition(n, 'y')}%`,
            backgroundColor: getParticleColor(stockpile.utilization_percent),
            animationDelay: `${n * 0.2}s`
          }"
        ></div>
        
        <!-- Percentage label -->
        <div class="absolute -top-4 right-0 z-10">
          <span class="text-xs font-bold px-1.5 py-0.5 rounded text-white bg-gray-800 bg-opacity-75">
            {{ Math.round(stockpile.utilization_percent) }}%
          </span>
        </div>
      </div>
    </div>
    
    <!-- Capacity and Quantity Info -->
    <div class="text-sm text-brand-gray mb-2">
      <span class="font-semibold">{{ formattedQuantity }}</span> / {{ formatNumber(stockpile.capacity) }} t
    </div>
    
    <!-- Material Name -->
    <div class="text-xs text-gray-500 italic truncate" v-if="stockpile.material_name">
      {{ stockpile.material_name }}
    </div>
    
    <!-- Material Age or Last FWO -->
    <div class="text-xs text-gray-500" v-if="stockpile.material_age_hours">
      Age: {{ Math.round(stockpile.material_age_hours) }} hours
    </div>
    <div class="text-xs text-gray-600 font-semibold" v-if="stockpile.last_fwo">
      Order: {{ stockpile.last_fwo }}
    </div>
    
    <!-- NDP Specific Fields -->
    <div v-if="stockpile.last_fwo && stockpile.last_fwo !== 'N/A'" class="mt-2 pt-2 border-t border-gray-200 space-y-1">
      <!-- Destination -->
      <div class="text-xs text-gray-500" v-if="stockpile.last_ordered_destination">
        <span class="font-medium">To:</span> {{ stockpile.last_ordered_destination }}
      </div>
      
      <!-- ETD -->
      <div class="text-xs text-gray-500" v-if="stockpile.last_fwo_etd">
        <span class="font-medium">ETD:</span> {{ formatDateTime(stockpile.last_fwo_etd) }}
      </div>
      
      <!-- Planned Quantity -->
      <div class="text-xs text-gray-500" v-if="stockpile.last_fwo_planned_quantity">
        <span class="font-medium">Planned:</span> {{ Math.round(stockpile.last_fwo_planned_quantity) }} t
      </div>
      
      <!-- Transporter -->
      <div class="text-xs text-gray-500" v-if="stockpile.last_fwo_planned_transporter">
        <span class="font-medium">By:</span> {{ stockpile.last_fwo_planned_transporter }}
      </div>
      
      <!-- Truck Completed Count -->
      <div class="text-xs text-green-600 font-medium" v-if="stockpile.truck_completed_count !== undefined">
        <span class="font-medium">Completed:</span> {{ stockpile.truck_completed_count }} trucks
      </div>
      
      <!-- First Truck Gate In -->
      <div class="text-xs text-blue-600" v-if="stockpile.first_truck_gate_in && stockpile.first_truck_gate_in !== 'N/A'">
        <span class="font-medium">1st Truck:</span> {{ formatDateTime(stockpile.first_truck_gate_in) }}
      </div>
    </div>
    
    <!-- Silo Loading (shown separately if no FWO) -->
    <div class="text-xs text-gray-500" v-if="stockpile.silo_loading && stockpile.silo_loading !== 'N/A'">
      Loading: {{ stockpile.silo_loading }}
    </div>

  </div>
</template>

<script>
import { computed, h } from 'vue'

export default {
  name: 'StockpileBar',
  props: {
    stockpile: {
      type: Object,
      required: true,
      default: () => ({
        name: '',
        capacity: 0,
        quantity: 0,
        material_name: '',
        material_age_hours: 0,
        utilization_percent: 0
      })
    },
    rounding: {
      type: Number,
      default: 0
    }
  },
  setup(props) {
    const formattedQuantity = computed(() => {
      if (props.rounding === 0) {
        return formatNumber(props.stockpile.quantity)
      } else {
        const rounded = Math.round(props.stockpile.quantity / props.rounding) * props.rounding
        return formatNumber(rounded)
      }
    })

    const getUtilizationColor = (percentage) => {
      if (percentage >= 90) return '#A7002C' // brand-red
      if (percentage >= 75) return '#F59E0B' // amber-500
      if (percentage >= 50) return '#EAB308' // yellow-500
      if (percentage >= 25) return '#22C55E' // green-500
      return '#333333' // brand-gray
    }

    const getParticleColor = (percentage) => {
      // Slightly darker versions of the main color for texture
      if (percentage >= 90) return '#8B0000' // darker red
      if (percentage >= 75) return '#D97706' // darker amber
      if (percentage >= 50) return '#CA8A04' // darker yellow
      if (percentage >= 25) return '#16A34A' // darker green
      return '#1F2937' // darker gray
    }

    const getParticleCount = (percentage) => {
      // Fewer particles for a cleaner look
      if (percentage > 80) return 4
      if (percentage > 50) return 3
      if (percentage > 20) return 2
      return percentage > 0 ? 1 : 0
    }

    const getRandomPosition = (seed, axis) => {
      // More controlled positioning for better pile appearance
      const random = Math.sin(seed * 12.9898) * 43758.5453
      const normalized = (random - Math.floor(random))
      
      if (axis === 'x') {
        // Keep particles more centered horizontally
        return 25 + (normalized * 50)
      } else {
        // Distribute particles vertically within the pile
        return 30 + (normalized * 40)
      }
    }

    const formatNumber = (num) => {
      // Round to whole number and show zero for negative values
      const roundedNum = Math.max(0, Math.round(Number(num)))
      return roundedNum.toLocaleString('en-US', { 
        minimumFractionDigits: 0, 
        maximumFractionDigits: 0 
      })
    }

    const formatDateTime = (dateTimeString) => {
      if (!dateTimeString || dateTimeString === 'N/A') return 'N/A'
      try {
        // Parse the UTC datetime from Odoo
        const date = new Date(dateTimeString + ' UTC')
        
        // Convert to UAE timezone (UTC+4)
        return date.toLocaleString('en-GB', { 
          day: '2-digit', 
          month: '2-digit', 
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          timeZone: 'Asia/Dubai'
        })
      } catch {
        return dateTimeString
      }
    }

    return {
      getUtilizationColor,
      getParticleColor,
      getParticleCount,
      getRandomPosition,
      formatNumber,
      formatDateTime,
      formattedQuantity
    }
  }
}
</script>

<style scoped>
.pile-container {
  position: relative;
  display: flex;
  align-items: end;
  justify-content: center;
  height: 100%;
}

.pile-shape {
  position: relative;
  /* Make it look like a natural pile - wider at base, narrower at top */
  border-radius: 80% 80% 20% 20% / 100% 100% 0% 0%;
  box-shadow: 
    inset -3px -3px 6px rgba(0, 0, 0, 0.3),
    inset 3px 3px 6px rgba(255, 255, 255, 0.2),
    0 3px 10px rgba(0, 0, 0, 0.2);
  transform-origin: bottom center;
  animation: pileGrow 0.8s ease-out;
  /* Add a slight 3D perspective */
  transform: perspective(100px) rotateX(5deg);
}

.pile-particle {
  position: absolute;
  width: 2px;
  height: 2px;
  border-radius: 50%;
  opacity: 0.7;
  animation: particleFloat 3s ease-in-out infinite;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

@keyframes pileGrow {
  0% {
    transform: perspective(100px) rotateX(5deg) scaleY(0);
    opacity: 0;
  }
  50% {
    transform: perspective(100px) rotateX(5deg) scaleY(1.05);
    opacity: 0.9;
  }
  100% {
    transform: perspective(100px) rotateX(5deg) scaleY(1);
    opacity: 1;
  }
}

@keyframes particleFloat {
  0%, 100% {
    transform: translateY(0px) scale(1);
  }
  50% {
    transform: translateY(-1px) scale(1.1);
  }
}

/* Subtle highlight on top of pile */
.pile-shape::before {
  content: '';
  position: absolute;
  top: 0;
  left: 25%;
  right: 25%;
  height: 40%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3) 0%, transparent 70%);
  border-radius: 80% 80% 50% 50%;
  pointer-events: none;
}

/* Shadow at base */
.pile-shape::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: -5px;
  right: -5px;
  height: 6px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.2), transparent);
  border-radius: 50%;
  pointer-events: none;
  filter: blur(2px);
}

.stockpile-item {
  background-color: #f9fafb;
  border-radius: 0.5rem;
  padding: 1rem;
  border: 1px solid #e5e7eb;
}
</style>
