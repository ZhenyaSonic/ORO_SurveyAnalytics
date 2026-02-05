<template>
  <v-table>
    <thead>
      <tr>
        <th class="text-left">Респондент</th>
        <th
          v-for="question in questions"
          :key="question.question_id"
          class="text-left"
        >
          {{ question.question_name }} ({{ question.question_type }})
        </th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="respondent in respondents" :key="respondent.respondent_id">
        <td>{{ respondent.respondent_id }}</td>
        <td
          v-for="response in respondent.responses"
          :key="response.question_id"
        >
          <v-tooltip
            v-if="response.question_type === 'SINGLE' || response.question_type === 'MULTIPLE'"
            location="top"
          >
            <template v-slot:activator="{ props }">
              <span v-bind="props">
                {{ formatCodes(response.value) }}
              </span>
            </template>
            <div>
              <div v-for="code in response.value" :key="code">
                {{ code }}: {{ getAnswerLabel(response.question_id, code) }}
              </div>
            </div>
          </v-tooltip>
          <span v-else>{{ response.value }}</span>
        </td>
      </tr>
    </tbody>
  </v-table>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'ResponsesTable',
  props: {
    responses: {
      type: Object,
      required: true
    },
    answerOptionsMap: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const respondents = computed(() => props.responses.respondents || [])
    
    const questions = computed(() => {
      if (respondents.value.length === 0) return []
      return respondents.value[0].responses.map(r => ({
        question_id: r.question_id,  // Теперь это будет имя (Q6), а не UUID
        question_name: r.question_name,
        question_type: r.question_type
      }))
    })

    const formatCodes = (codes) => {
      if (Array.isArray(codes)) {
        return codes.join(', ')
      }
      return codes || ''
    }

    const getAnswerLabel = (questionName, code) => {
      // Нужно получить UUID вопроса по его имени
      // Пока используем имя как ключ
      const options = props.answerOptionsMap[questionName] || []
      const option = options.find(opt => opt.code === code)
      return option ? option.label : `Code ${code}`
    }

    return {
      respondents,
      questions,
      formatCodes,
      getAnswerLabel
    }
  }
}
</script>