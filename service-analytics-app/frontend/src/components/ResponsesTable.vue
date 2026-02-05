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
                <!-- Используем безопасное форматирование -->
                {{ safeFormatValue(response) }}
              </span>
            </template>
            <div>
              <div v-if="response.question_type === 'SINGLE'">
                {{ safeFormatValue(response) }}: {{ getAnswerLabel(response.question_id, response.value) }}
              </div>
              <div v-else-if="response.question_type === 'MULTIPLE'">
                <div v-for="code in response.value" :key="code">
                  {{ code }}: {{ getAnswerLabel(response.question_id, code) }}
                </div>
              </div>
            </div>
          </v-tooltip>
          <span v-else>{{ response.value || '' }}</span>
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
    console.log('=== ResponsesTable DEBUG ===')
    console.log('Responses data:', props.responses)
    console.log('Answer options map:', props.answerOptionsMap)

    const respondents = computed(() => {
      const respondents = props.responses.respondents || []
      console.log('Number of respondents:', respondents.length)
      if (respondents.length > 0) {
        console.log('Sample responses:', respondents[0].responses)
      }
      return respondents
    })
    
    const questions = computed(() => {
      if (respondents.value.length === 0) return []
      return respondents.value[0].responses.map(r => ({
        question_id: r.question_id,
        question_name: r.question_name,
        question_type: r.question_type
      }))
    })

    const safeFormatValue = (response) => {
      console.log('safeFormatValue called:', {
        question: response.question_name,
        type: response.question_type,
        value: response.value,
        valueType: typeof response.value
      })
      
      if (response.question_type === 'SINGLE') {
        // Безопасное форматирование для SINGLE вопросов
        // Учитываем, что 0 - валидное значение
        if (response.value === null || response.value === undefined) {
          return ''
        }
        // Явно преобразуем в строку
        return String(response.value)
      } else if (response.question_type === 'MULTIPLE') {
        if (Array.isArray(response.value)) {
          return response.value.join(', ')
        }
        return ''
      }
      // Для TEXT вопросов
      return response.value || ''
    }

    const getAnswerLabel = (questionId, code) => {
      console.log(`getAnswerLabel: questionId=${questionId}, code=${code} (${typeof code})`)
      const options = props.answerOptionsMap[questionId] || []
      
      // Приводим код к числу для сравнения (опции хранятся как числа)
      const numCode = Number(code)
      const option = options.find(opt => {
        // Опции могут храниться как числа или строки
        const optCode = Number(opt.code)
        return optCode === numCode
      })
      
      return option ? option.label : `Code ${code}`
    }

    return {
      respondents,
      questions,
      safeFormatValue,
      getAnswerLabel
    }
  }
}
</script>