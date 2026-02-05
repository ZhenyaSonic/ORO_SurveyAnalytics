import { defineStore } from 'pinia'
import { surveysApi } from '../api/surveys'

export const useSurveysStore = defineStore('surveys', {
  state: () => ({
    surveys: [],
    questions: {},
    loading: false,
    error: null
  }),

  actions: {
    async fetchSurveys() {
      this.loading = true
      this.error = null
      try {
        const response = await surveysApi.getSurveys()
        this.surveys = response.data
      } catch (error) {
        this.error = error.message
        console.error('Error fetching surveys:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchSurveyQuestions(surveyId) {
      this.loading = true
      this.error = null
      try {
        const response = await surveysApi.getSurveyQuestions(surveyId)
        this.questions[surveyId] = response.data
        return response.data
      } catch (error) {
        this.error = error.message
        console.error('Error fetching questions:', error)
        throw error
      } finally {
        this.loading = false
      }
    }
  }
})

