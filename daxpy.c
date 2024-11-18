#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

typedef struct {
    double *x;
    double *y;
    double a;
    int start;
    int end;
} thread_data_t;

// DAXPY kernel function for each thread
void *daxpy_thread(void *arg) {
    thread_data_t *data = (thread_data_t *)arg;
    for (int i = data->start; i < data->end; i++) {
        data->y[i] = data->a * data->x[i] + data->y[i];
    }
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        fprintf(stderr, "Usage: %s <vector_size> <a> <num_threads> <output_file>\n", argv[0]);
        return 1;
    }

    int vector_size = atoi(argv[1]);
    double a = atof(argv[2]);
    int num_threads = atoi(argv[3]);
    char *output_filename = argv[4];

    double *x = (double *)malloc(vector_size * sizeof(double));
    double *y = (double *)malloc(vector_size * sizeof(double));

    for (int i = 0; i < vector_size; i++) {
        x[i] = i;
        y[i] = i * 2;
    }

    pthread_t threads[num_threads];
    thread_data_t thread_data[num_threads];

    int chunk_size = vector_size / num_threads;
    int remainder = vector_size % num_threads;

    for (int i = 0; i < num_threads; i++) {
        thread_data[i].x = x;
        thread_data[i].y = y;
        thread_data[i].a = a;
        thread_data[i].start = i * chunk_size;
        thread_data[i].end = (i + 1) * chunk_size;

        // Distribute the remainder among the threads
        if (i < remainder) {
            thread_data[i].end++;
            thread_data[i].start += i; 
        } else {
            thread_data[i].start += remainder;
        }

        pthread_create(&threads[i], NULL, daxpy_thread, (void *)&thread_data[i]);
    }

    // Wait for all threads to finish
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    // Write the output to a file (optional)
    FILE *outfile = fopen(output_filename, "w");
    if (outfile == NULL) {
        perror("Error opening output file");
        return 1;
    }
    for (int i = 0; i < vector_size; i++) {
        fprintf(outfile, "%.2f\n", y[i]);
    }
    fclose(outfile);

    // Free allocated memory
    free(x);
    free(y);

    return 0;
}
