#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
//#include <errno.h>


int main(int argc, char *args[])
{
    char *uc;
    fprintf(stdout, "Starting\n");
    fflush(stdout);

    for (int i = 1; i <= 5; i++)
    {
        sleep(3);
        uc = (char *) malloc(i * 131072 * sizeof(char));  //128kB
        //uc = (char *) malloc(i * sizeof(char));  //128kB
        if (uc == NULL)
        {
            perror("ERROR: ");
        }
        else
        {
            fprintf(stdout, "Memory alocked\n");
            fflush(stdout);
            free(uc);
        }
    }
    return 0;
}
     
