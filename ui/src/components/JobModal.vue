<template>
  <v-dialog :model-value="isOpen" max-width="550px" @click:outside="onClose">
    <v-card class="section">
      <v-card-title class="header title">New job</v-card-title>
      <v-card-text class="mt-3">
        <v-row>
          <v-col>
            <v-select
              v-model="selected"
              :items="types"
              :menu-props="{ offsetY: true, maxWidth: 500 }"
              label="Type"
              item-title="title"
              id="type"
              density="comfortable"
              hide-details
            >
              <template v-slot:item="{ item, props }">
                <v-list-item v-bind="props">
                  <v-list-item-subtitle>
                    {{ item.raw.description }}
                  </v-list-item-subtitle>
                </v-list-item>
              </template>
            </v-select>
          </v-col>
        </v-row>
        <v-row v-if="selected === 'genderize'">
          <v-col>
            <v-checkbox
              v-model="forms.genderize.exclude"
              label="Exclude individuals in RecommenderExclusionTerm list"
              id="genderize_exclude"
            />
            <v-checkbox
              v-model="forms.genderize.noStrictMatching"
              label="Disable strict name validation"
              id="genderize_noStrictMatching"
            />
          </v-col>
        </v-row>
        <v-form v-if="selected === 'unify'">
          <v-row class="ma-0 mt-2">
            <v-col class="pa-0 mb-3">
              <v-checkbox
                v-model="forms.unify.exclude"
                label="Exclude individuals in RecommenderExclusionTerm list"
                density="comfortable"
                hide-details
              />
              <v-checkbox
                v-model="forms.unify.strict"
                label="Exclude individuals with invalid email addresses and names"
                density="comfortable"
                hide-details
              />
            </v-col>
          </v-row>
          <v-row class="ma-0">
            <v-col class="pa-0">
              <fieldset>
                <legend class="subheader text--secondary">
                  Unify profiles based on their:
                </legend>
                <v-checkbox
                  v-model="forms.unify.criteria"
                  label="Name"
                  value="name"
                  density="comfortable"
                  hide-details
                />
                <v-checkbox
                  v-model="forms.unify.criteria"
                  label="Email"
                  value="email"
                  density="comfortable"
                  hide-details
                />
                <v-checkbox
                  v-model="forms.unify.criteria"
                  label="Username"
                  value="username"
                  density="comfortable"
                  hide-details
                />
                <v-checkbox
                  class="ml-4"
                  v-model="forms.unify.matchSource"
                  label="Only unify identities that share the same source"
                  density="comfortable"
                  hide-details
                />
              </fieldset>
            </v-col>
          </v-row>
        </v-form>
        <v-form v-if="selected === 'recommendMatches'">
          <v-row class="ma-0 mt-2">
            <v-col class="pa-0 mb-3">
              <v-checkbox
                v-model="forms.recommendMatches.exclude"
                label="Exclude individuals in RecommenderExclusionTerm list"
                density="comfortable"
                hide-details
              />
              <v-checkbox
                v-model="forms.recommendMatches.strict"
                label="Exclude individuals with invalid email adresses and names"
                density="comfortable"
                hide-details
              />
            </v-col>
          </v-row>
          <v-row class="ma-0">
            <v-col class="pa-0">
              <fieldset>
                <legend class="subheader text--secondary">
                  Recommend matches based on:
                </legend>
                <v-checkbox
                  v-model="forms.recommendMatches.criteria"
                  label="Name"
                  value="name"
                  density="comfortable"
                  hide-details
                />
                <v-checkbox
                  v-model="forms.recommendMatches.criteria"
                  label="Email"
                  value="email"
                  density="comfortable"
                  hide-details
                />
                <v-checkbox
                  v-model="forms.recommendMatches.criteria"
                  label="Username"
                  value="username"
                  density="comfortable"
                  hide-details
                />
                <v-checkbox
                  class="ml-4"
                  v-model="forms.recommendMatches.matchSource"
                  label="Only recommend identities that share the same source"
                  density="comfortable"
                  hide-details
                />
              </fieldset>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary darken-1" variant="text" @click="onClose">
          Cancel
        </v-btn>
        <v-btn
          :disabled="!selected"
          color="primary"
          id="confirm"
          variant="flat"
          @click="onSave"
        >
          Confirm
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
const jobTypes = [
  {
    title: "Affiliate",
    value: "affiliate",
    description:
      "Affiliate individuals to organizations using recommendations.",
  },
  {
    title: "Genderize",
    value: "genderize",
    description:
      "Autocomplete the gender information of individuals using genderize.io recommendations. ",
  },
  {
    title: "Unify",
    value: "unify",
    description: "Merge individuals by using matching recommendations.",
  },
  {
    title: "Recommend matches",
    value: "recommendMatches",
    description: "Recommend identity matches for individuals.",
  },
];
const defaultForms = {
  genderize: {
    exclude: true,
    noStrictMatching: false,
  },
  unify: {
    criteria: ["name", "email", "username"],
    exclude: true,
    strict: true,
    matchSource: false,
  },
  recommendMatches: {
    criteria: ["name", "email", "username"],
    exclude: true,
    strict: true,
    matchSource: false,
  },
};

export default {
  name: "JobModal",
  props: {
    isOpen: {
      type: Boolean,
      required: true,
    },
    types: {
      type: Array,
      required: false,
      default: () => jobTypes,
    },
  },
  data() {
    return {
      selected: null,
      forms: defaultForms,
    };
  },
  methods: {
    onClose() {
      this.$emit("update:isOpen", false);
      this.selected = null;
      this.forms = Object.assign({}, this.forms, defaultForms);
    },
    onSave() {
      this.$emit(this.selected, this.forms[this.selected]);
      this.onClose();
    },
  },
};
</script>

<style lang="scss" scoped>
@import "../styles/index.scss";

.v-list-item .v-list-item__subtitle {
  max-width: 490px;
  overflow: visible;
  white-space: normal;
}
</style>
