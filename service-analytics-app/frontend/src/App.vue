<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-app-bar-title>Survey Analytics</v-app-bar-title>
    </v-app-bar>
    
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'App'
}
</script>

