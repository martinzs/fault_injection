#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>

int main(int argc, char *args[])
{
    for (int i = 0; i < 10; i++)
    {
        {
            if (fprintf(stdout, "%d\n", i) < 0)
                perror("ERROR");
            else
                if (fflush(stdout) == EOF)
                    perror("ERROR");
        }
        sleep(3);
    }
}
