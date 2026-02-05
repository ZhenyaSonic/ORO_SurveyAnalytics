<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Настройка отображения ответов</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>Параметры отображения</v-card-title>
          <v-card-text>
            <v-form ref="form">
              <v-select
                v-model="selectedSurvey"
                :items="surveys"
                item-title="id"
                item-value="id"
                label="Опрос"
                :loading="loading"
                @update:model-value="onSurveyChange"
              ></v-select>

              <v-textarea
                v-model="questionIdsText"
                label="Список вопросов"
                hint="Введите ID вопросов через запятую"
                :error-messages="questionIdsErrors"
                rows="3"
                class="mt-4"
              ></v-textarea>

              <v-btn
                color="primary"
                @click="validateQuestions"
                :loading="validating"
                class="mt-4"
              >
                Проверить заполнение
              </v-btn>

              <v-alert
                v-if="validationError"
                type="error"
                class="mt-4"
              >
                {{ validationError }}
              </v-alert>

              <v-btn
                v-if="validationSuccess"
                color="success"
                @click="showDialog = true"
                class="mt-4"
              >
                Отобразить
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog with responses table -->
    <v-dialog v-model="showDialog" max-width="90%" scrollable>
      <v-card>
        <v-card-title>
          <span class="text-h5">Ответы респондентов</span>
        </v-card-title>
        <v-card-text>
          <ResponsesTable
            v-if="responsesData"
            :responses="responsesData"
            :answer-options-map="answerOptionsMap"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="showDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useSurveysStore } from '../stores/surveys'
import { surveysApi } from '../api/surveys'
import ResponsesTable from '../components/ResponsesTable.vue'

export default {
  name: 'Home',
  components: {
    ResponsesTable
  },
  setup() {
    const surveysStore = useSurveysStore()
    const selectedSurvey = ref(null)
    const questionIdsText = ref('')
    const questionIdsErrors = ref([])
    const validating = ref(false)
    const validationError = ref('')
    const validationSuccess = ref(false)
    const showDialog = ref(false)
    const responsesData = ref(null)
    const answerOptionsMap = ref({})

    const surveys = computed(() => surveysStore.surveys)
    const loading = computed(() => surveysStore.loading)

    onMounted(async () => {
      await surveysStore.fetchSurveys()
    })

    const onSurveyChange = async () => {
      questionIdsText.value = ''
      validationError.value = ''
      validationSuccess.value = false
      responsesData.value = null
    }

    const parseQuestionIds = () => {
      return questionIdsText.value
        .split(',')
        .map(id => id.trim())
        .filter(id => id.length > 0)
    }

    const validateQuestions = async () => {
      if (!selectedSurvey.value) {
        questionIdsErrors.value = ['Выберите опрос']
        return
      }

      const questionIds = parseQuestionIds()
      if (questionIds.length === 0) {
        questionIdsErrors.value = ['Введите хотя бы один ID вопроса']
        return
      }

      validating.value = true
      validationError.value = ''
      validationSuccess.value = false
      questionIdsErrors.value = []

      try {
        const response = await surveysApi.validateQuestions(
          selectedSurvey.value,
          questionIds
        )

        if (response.data.valid) {
          validationSuccess.value = true
          questionIdsErrors.value = []
        } else {
          validationError.value = 'Обнаружены ошибки: ' + response.data.errors.join(', ')
          questionIdsErrors.value = response.data.errors
        }
      } catch (error) {
        validationError.value = 'Ошибка при проверке: ' + (error.response?.data?.detail || error.message)
        questionIdsErrors.value = ['Ошибка при проверке']
      } finally {
        validating.value = false
      }
    }

    const loadResponses = async () => {
      if (!selectedSurvey.value || !validationSuccess.value) {
        return
      }

      const questionIds = parseQuestionIds()
      
      try {
        console.log('=== FRONTEND DEBUG START ===')
        
        // Load responses
        const responsesResponse = await surveysApi.getResponses(
          selectedSurvey.value,
          questionIds
        )
        responsesData.value = responsesResponse.data
        
        // Глубокая проверка данных
        console.log('Full API Response:', JSON.stringify(responsesResponse.data, null, 2))
        
        if (responsesData.value.respondents && responsesData.value.respondents.length > 0) {
          const firstRespondent = responsesData.value.respondents[0]
          console.log('\n=== FIRST RESPONDENT DETAILS ===')
          console.log('Respondent ID:', firstRespondent.respondent_id)
          
          firstRespondent.responses.forEach((resp, idx) => {
            console.log(`\nResponse ${idx + 1}:`)
            console.log('  Question ID:', resp.question_id)
            console.log('  Question Name:', resp.question_name)
            console.log('  Question Type:', resp.question_type)
            console.log('  Value:', resp.value)
            console.log('  Value Type:', typeof resp.value)
            console.log('  Is Number?', typeof resp.value === 'number')
            console.log('  Is Zero?', resp.value === 0)
            console.log('  String Value:', String(resp.value))
          })
        }
        
        // Load answer options for SINGLE/MULTIPLE questions
        const questions = surveysStore.questions[selectedSurvey.value] || []
        const choiceQuestionIds = questions
          .filter(q => q.type === 'SINGLE' || q.type === 'MULTIPLE')
          .map(q => q.id)
        
        console.log('\n=== LOADING ANSWER OPTIONS ===')
        console.log('Choice question IDs:', choiceQuestionIds)
        
        if (choiceQuestionIds.length > 0) {
          const optionsResponse = await surveysApi.getAnswerOptions(choiceQuestionIds)
          answerOptionsMap.value = optionsResponse.data
          
          // Проверяем опции ответов
          console.log('Answer options loaded:', answerOptionsMap.value)
          
          // Проверяем типы данных в опциях
          Object.keys(answerOptionsMap.value).forEach(qId => {
            const options = answerOptionsMap.value[qId]
            if (options && options.length > 0) {
              console.log(`Question ${qId}: first option code=${options[0].code}, type=${typeof options[0].code}`)
            }
          })
        }
        
        console.log('=== FRONTEND DEBUG END ===')
      } catch (error) {
        console.error('Error loading responses:', error)
        validationError.value = 'Ошибка при загрузке ответов: ' + (error.response?.data?.detail || error.message)
      }
    }

    watch(showDialog, (newVal) => {
      if (newVal && !responsesData.value) {
        loadResponses()
      }
    })

    return {
      selectedSurvey,
      questionIdsText,
      questionIdsErrors,
      validating,
      validationError,
      validationSuccess,
      showDialog,
      responsesData,
      answerOptionsMap,
      surveys,
      loading,
      onSurveyChange,
      validateQuestions
    }
  }
}
</script>