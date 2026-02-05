<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Все ответы по опросу {{ surveyId }}</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card v-if="loading">
          <v-card-text>
            <v-progress-linear indeterminate color="primary"></v-progress-linear>
            <div class="text-center mt-4">Загрузка данных...</div>
          </v-card-text>
        </v-card>

        <v-card v-else-if="error">
          <v-card-text>
            <v-alert type="error">{{ error }}</v-alert>
          </v-card-text>
        </v-card>

        <v-card v-else-if="responsesData">
          <v-card-text>
            <ResponsesTable
              :responses="responsesData"
              :answer-options-map="answerOptionsMap"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { ref, onMounted } from 'vue'
import { surveysApi } from '../api/surveys'
import ResponsesTable from '../components/ResponsesTable.vue'

export default {
  name: 'SurveyView',
  components: {
    ResponsesTable
  },
  props: {
    surveyId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const loading = ref(true)
    const error = ref(null)
    const responsesData = ref(null)
    const answerOptionsMap = ref({})

    const loadData = async () => {
      loading.value = true
      error.value = null

      try {
        // Load all responses
        const responsesResponse = await surveysApi.getAllResponses(props.surveyId)
        responsesData.value = responsesResponse.data

        // Load answer options
        const questions = responsesData.value.respondents[0]?.responses || []
        const choiceQuestionIds = questions
          .filter(q => q.question_type === 'SINGLE' || q.question_type === 'MULTIPLE')
          .map(q => q.question_id)
        
        if (choiceQuestionIds.length > 0) {
          const optionsResponse = await surveysApi.getAnswerOptions(choiceQuestionIds)
          answerOptionsMap.value = optionsResponse.data
        }
      } catch (err) {
        error.value = err.response?.data?.detail || err.message || 'Ошибка при загрузке данных'
        console.error('Error loading survey data:', err)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadData()
    })

    return {
      loading,
      error,
      responsesData,
      answerOptionsMap
    }
  }
}
</script>

