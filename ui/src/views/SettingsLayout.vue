<template>
  <v-main>
    <div class="d-flex pa-8">
      <v-navigation-drawer
        width="300"
        color="transparent"
        class="pa-8"
        floating
        permanent
      >
        <v-list color="primary" density="comfortable" nav>
          <v-list-item-title class="text-subtitle-1 font-weight-medium mb-2">
            Settings
          </v-list-item-title>
          <v-list-item
            :to="{ name: 'SettingsGeneral' }"
            active-class="primary--text white"
            link
          >
            <v-list-item-title>General</v-list-item-title>
          </v-list-item>
          <v-list-item
            :to="{ name: 'SettingsSync' }"
            active-class="primary--text white"
            link
          >
            <v-list-item-title>Synchronization</v-list-item-title>
          </v-list-item>
          <v-list-item
            :to="{ name: 'SettingsJobs' }"
            active-class="primary--text white"
            link
          >
            <v-list-item-title>Jobs</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-navigation-drawer>
      <v-container class="pa-0 pr-6">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </v-container>
    </div>
  </v-main>
</template>
<script>
export default {
  name: "SettingLayout",
};
</script>
<style lang="scss" scoped>
@media (min-width: 1904px) {
  .container {
    max-width: 1185px;
  }
}
</style>
