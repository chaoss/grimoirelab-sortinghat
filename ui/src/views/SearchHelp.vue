<template>
  <v-main>
    <v-card class="mx-auto elevation-0 mt-6 section" max-width="800px">
      <v-card-title class="header"> Search syntax </v-card-title>
      <v-card-text class="pa-8 pt-0">
        <p class="text-subtitle-2">Search by term</p>
        <p class="text-body-2">
          You can find individuals whose identities contain a particular term in
          their name, email address or username by entering the term on the
          search box. You can combine this query with any filters, for example
          <code>John lastUpdated:>2020-11-01</code>.
        </p>
        <p class="text-subtitle-2">Filter by last updated date</p>
        <p class="text-body-2">
          You can filter individuals based on when they were modified, using the
          <code>lastUpdated</code> filter.
        </p>
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr>
                <th class="text-left" width="30%">Filter</th>
                <th class="text-left">Explanation</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td width="30%"><code>lastUpdated:>YYYY-MM-DD</code></td>
                <td>
                  Matches individuals that were updated after the given date.
                </td>
              </tr>
              <tr>
                <td width="30%"><code>lastUpdated:>=YYYY-MM-DD</code></td>
                <td>
                  Matches individuals that were updated on or after the given
                  date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>lastUpdated:&lt;YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were updated before the given date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>lastUpdated:&lt;=YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were updated on or before the given
                  date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>lastUpdated:YYYY-MM-DD..YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were updated between the given dates.
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>

        <p class="text-subtitle-2">Search for bots</p>
        <p class="text-body-2">
          You can search for individuals based on whether they are marked as
          bots, using the <code>isBot:true</code> and <code>isBot:false</code>
          filters.
        </p>
        <p class="text-subtitle-2">Filter by gender</p>
        <p class="text-body-2">
          You can search for individuals based on their gender, using the
          <code>gender</code> filter. Genders that include spaces should be
          wrapped in double quotes. For example:
          <code>gender:"non binary"</code>.
        </p>

        <p class="text-subtitle-2">Filter by country</p>
        <p class="text-body-2">
          You can filter individuals based on their country using the
          <code>country</code> filter.
        </p>
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr>
                <th class="text-left" width="30%">Filter</th>
                <th class="text-left">Explanation</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td width="30%"><code>country:name</code></td>
                <td>
                  Matches individuals from the given country. Country names that
                  include spaces should be wrapped in double quotes. For
                  example: <code>country:"Dominican Republic"</code>
                </td>
              </tr>
              <tr>
                <td width="30%"><code>country:code</code></td>
                <td>
                  Matches individuals from a given country using ISO (Alpha-2
                  and Alpha-3) country codes. For example:
                  <code>country:USA</code>.
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>

        <p class="text-subtitle-2">Filter by data source</p>
        <p class="text-body-2">
          You can search for individuals based on the data source of their
          identities, using the <code>source</code> filter. Source names that
          include spaces should be wrapped between double quotes. For example:
          <code>source:"Stack Exchange"</code>.
        </p>

        <p class="text-subtitle-2">Filter by enrollment</p>
        <p class="text-body-2">
          You can search for individuals based on the organizations they are
          enrolled in, using the <code>enrollment</code> filter. Organizations
          that include spaces should be wrapped between double quotes. For
          example: <code>enrollment:"Dumbledore's Army"</code>.
        </p>

        <p class="text-subtitle-2">Filter by enrollment date</p>
        <p class="text-body-2">
          You can filter individuals based on when they were affiliated to an
          organization, using the <code>enrollmentDate</code> filter.
        </p>
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr>
                <th class="text-left" width="30%">Filter</th>
                <th class="text-left">Explanation</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td width="30%"><code>enrollmentDate:>YYYY-MM-DD</code></td>
                <td>
                  Matches individuals that were affiliated to an organization
                  after the given date.
                </td>
              </tr>
              <tr>
                <td width="30%"><code>enrollmentDate:>=YYYY-MM-DD</code></td>
                <td>
                  Matches individuals that were affiliated to an organization on
                  or after the given date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>enrollmentDate:&lt;YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were affiliated to an organization
                  before the given date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>enrollmentDate:&lt;=YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were affiliated to an organization on
                  or before the given date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>enrollmentDate:YYYY-MM-DD..YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were affiliated to an organization
                  between the given dates.
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>

        <p class="text-subtitle-2">Filter by enrollment status</p>
        <p class="text-body-2">
          You can search for individuals based on whether they have any
          affiliation, using the <code>isEnrolled:true</code> and
          <code>isEnrolled:false</code> filters.
        </p>

        <p class="text-subtitle-2">Filter by review status</p>
        <p class="text-body-2">
          You can search for individuals based on whether they have been marked
          as reviewed, using the <code>isReviewed:true</code> and
          <code>isReviewed:false</code> filters.
        </p>

        <p class="text-subtitle-2">Filter by review date</p>
        <p class="text-body-2">
          You can filter individuals based on when they were last marked as
          reviewed, using the <code>lastReviewed</code> filter.
        </p>
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr>
                <th class="text-left" width="30%">Filter</th>
                <th class="text-left">Explanation</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td width="30%"><code>lastReviewed:>YYYY-MM-DD</code></td>
                <td>
                  Matches individuals that were reviewed after the given date.
                </td>
              </tr>
              <tr>
                <td width="30%"><code>lastReviewed:>=YYYY-MM-DD</code></td>
                <td>
                  Matches individuals that were reviewed on or after the given
                  date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>lastReviewed:&lt;YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were reviewed before the given date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>lastReviewed:&lt;=YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were reviewed on or before the given
                  date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>lastReviewed:YYYY-MM-DD..YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were reviewed between the given
                  dates.
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-card-text>
    </v-card>
  </v-main>
</template>

<script>
export default {
  name: "SearchHelp",
};
</script>
<style scoped>
.text-subtitle-2 {
  padding-bottom: 1.2rem;
  padding-top: 1.654rem;
  font-size: 1rem;
}

th,
td {
  padding: 1.09rem 0;
}

th {
  font-size: 0.813rem;
  font-weight: 500;
}

td {
  border-top: thin solid rgba(0, 0, 0, 0.08);
}

td:first-child {
  padding-right: 1.09rem;
}

code {
  border-radius: 4px;
  font-size: 90%;
  line-height: 1.25rem;
  padding: 0.1rem 0.25rem;
  background-color: #f2f3f5;
}
</style>
