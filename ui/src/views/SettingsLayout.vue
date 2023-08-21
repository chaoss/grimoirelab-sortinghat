<template>
  <v-main>
    <div class="d-flex pa-8">
      <v-navigation-drawer width="300" color="transparent" floating permanent>
        <v-list class="pr-6 pt-0" dense nav>
          <v-list-item-content class="pt-0">
            <v-list-item-title class="text-subtitle-1 font-weight-medium">
              Settings
            </v-list-item-title>
          </v-list-item-content>
          <v-list-item
            :to="{ name: 'SettingsGeneral' }"
            active-class="primary--text white"
            link
          >
            <v-list-item-content>
              <v-list-item-title>General</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          <v-list-item
            :to="{ name: 'SettingsSync' }"
            active-class="primary--text white"
            link
          >
            <v-list-item-content>
              <v-list-item-title>Synchronization</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          <v-list-item
            :to="{ name: 'SettingsJobs' }"
            active-class="primary--text white"
            link
          >
            <v-list-item-content>
              <v-list-item-title>Jobs</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-navigation-drawer>
      <v-container class="pa-0 pr-6">
        <transition name="fade" mode="out-in">
          <router-view />
        </transition>
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
